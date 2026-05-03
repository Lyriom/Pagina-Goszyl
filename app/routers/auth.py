"""Rutas de autenticacion: login / callback / logout (Keycloak SSO)."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from loguru import logger
from sqlalchemy import select

from app.auth.dependencies import SESSION_KEY, DBSession
from app.auth.keycloak import KeycloakAuthError, keycloak_client
from app.models.user import User, UserRole
from app.schemas.user import SessionUser

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
async def login(request: Request) -> RedirectResponse:
    """Inicia el flujo Authorization Code redirigiendo a Keycloak."""
    url, state = keycloak_client.build_login_url()
    request.session["oauth_state"] = state
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


@router.get("/callback")
async def callback(
    request: Request,
    db: DBSession,
    code: str = Query(...),
    state: str | None = Query(None),
    error: str | None = Query(None),
) -> RedirectResponse:
    """Recibe el code de Keycloak, valida JWT y crea/actualiza el usuario."""
    if error:
        logger.warning("Keycloak devolvio error: {}", error)
        raise HTTPException(status_code=400, detail=f"Error de Keycloak: {error}")

    expected_state = request.session.pop("oauth_state", None)
    if not expected_state or not state or not secrets.compare_digest(expected_state, state):
        logger.warning("State OAuth invalido (posible CSRF)")
        raise HTTPException(status_code=400, detail="Estado OAuth invalido")

    try:
        tokens = await keycloak_client.exchange_code_for_tokens(code)
    except KeycloakAuthError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e

    access_token = tokens.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Keycloak no devolvio access_token")

    try:
        claims = await keycloak_client.decode_and_validate(access_token)
    except KeycloakAuthError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e

    keycloak_id = claims.get("sub")
    if not keycloak_id:
        raise HTTPException(status_code=401, detail="JWT sin claim 'sub'")

    username = claims.get("preferred_username") or claims.get("email") or keycloak_id
    email = claims.get("email") or f"{username}@local"
    full_name = claims.get("name")

    roles = keycloak_client.extract_roles(claims)
    app_role = keycloak_client.pick_app_role(roles)

    # --- upsert local del usuario federado ---
    existing = (
        await db.execute(select(User).where(User.keycloak_id == keycloak_id))
    ).scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if existing is None:
        user = User(
            keycloak_id=keycloak_id,
            username=username,
            email=email,
            full_name=full_name,
            role=app_role if app_role in (r.value for r in UserRole) else UserRole.USER.value,
            last_login_at=now,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info("Nuevo usuario federado: {} ({})", user.username, user.role)
    else:
        existing.username = username
        existing.email = email
        existing.full_name = full_name
        if app_role in (r.value for r in UserRole):
            existing.role = app_role
        existing.last_login_at = now
        await db.commit()
        await db.refresh(existing)
        user = existing

    # --- guardar en sesion server-side firmada ---
    session_user = SessionUser(
        id=user.id,
        keycloak_id=user.keycloak_id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        roles=roles,
    )
    request.session[SESSION_KEY] = session_user.model_dump(mode="json")

    next_url = request.session.pop("next", None) or "/admin"
    return RedirectResponse(url=next_url, status_code=status.HTTP_302_FOUND)


@router.get("/logout")
async def logout(request: Request) -> RedirectResponse:
    """Cierra la sesion local y redirige al logout de Keycloak."""
    request.session.clear()
    return RedirectResponse(
        url=keycloak_client.build_logout_url(),
        status_code=status.HTTP_302_FOUND,
    )
