"""Dependencias FastAPI para autenticacion y autorizacion.

La sesion se serializa en una cookie firmada (SessionMiddleware con
itsdangerous). Solo guardamos el minimo necesario: id, keycloak_id,
roles, etc. Los tokens crudos no salen al cliente.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.schemas.user import SessionUser

SESSION_KEY = "user"


def _load_session_user(request: Request) -> SessionUser | None:
    raw = request.session.get(SESSION_KEY)
    if not raw:
        return None
    try:
        return SessionUser.model_validate(raw)
    except Exception:  # cookie corrupta / formato viejo
        request.session.pop(SESSION_KEY, None)
        return None


async def get_current_user(
    request: Request,
) -> SessionUser | None:
    """Retorna el usuario en sesion o None. No lanza errores."""
    return _load_session_user(request)


async def require_login(
    request: Request,
) -> SessionUser:
    """Exige sesion activa. Si no hay, redirige a /auth/login.

    En FastAPI las dependencias no pueden devolver un Response directamente,
    pero si lanzamos `HTTPException` con un `Location` header obtenemos el
    mismo efecto. Para HTML preferimos `RedirectResponse` mediante
    `from_response`.
    """
    user = _load_session_user(request)
    if user is None:
        # Guardamos la URL original para volver tras login.
        request.session["next"] = str(request.url)
        raise _redirect_exception("/auth/login")
    return user


def require_role(*roles: str) -> Callable[..., SessionUser]:
    """Factory de dependencia: exige que el usuario tenga al menos uno de los roles."""

    async def _checker(
        user: Annotated[SessionUser, Depends(require_login)],
    ) -> SessionUser:
        if settings.is_admin_email(user.email):
            return user
        if not user.has_any_role(*roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para acceder a este recurso.",
            )
        return user

    return _checker


def _redirect_exception(location: str) -> HTTPException:
    """HTTPException 307 con header Location -> equivalente a un redirect."""
    return HTTPException(
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        detail="Redirect",
        headers={"Location": location},
    )


# Atajo: sesion DB inyectada
DBSession = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[SessionUser | None, Depends(get_current_user)]
RequiredUser = Annotated[SessionUser, Depends(require_login)]
