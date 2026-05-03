"""Zona privada (admin/editor): dashboard y CRUD de posts."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse, Response
from loguru import logger
from sqlalchemy import select

from app.auth.dependencies import DBSession, RequiredUser, require_role
from app.models.post import Post, PostStatus
from app.models.user import User
from app.schemas.post import PostCreate, PostUpdate
from app.schemas.user import SessionUser
from app.services import post_service
from app.templating import templates

router = APIRouter(prefix="/admin", tags=["admin"])

EditorOrAdmin = Annotated[SessionUser, Depends(require_role("editor", "admin"))]


async def _resolve_user_or_404(db, session_user: SessionUser) -> User:
    """Carga el `User` ORM desde la sesion (necesario para FKs)."""
    user = (
        await db.execute(select(User).where(User.id == session_user.id))
    ).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return user


# ---------------- Dashboard ----------------
@router.get("", response_class=Response)
@router.get("/", response_class=Response)
async def dashboard(
    request: Request,
    db: DBSession,
    user: EditorOrAdmin,
):
    """Resumen general: totales y posts recientes."""
    counts = await post_service.count_posts_by_status(db)
    is_admin = user.role == "admin"
    posts = await post_service.list_admin_posts(
        db,
        author_id=None if is_admin else user.id,
    )
    return templates.TemplateResponse(
        request,
        "admin/dashboard.html",
        {
            "user": user,
            "counts": counts,
            "recent_posts": posts[:5],
            "page_title": "Dashboard",
        },
    )


# ---------------- Listado de posts ----------------
@router.get("/posts", response_class=Response)
async def list_posts(
    request: Request,
    db: DBSession,
    user: EditorOrAdmin,
    status_filter: str | None = Query(None, alias="status"),
):
    is_admin = user.role == "admin"
    posts = await post_service.list_admin_posts(
        db,
        author_id=None if is_admin else user.id,
        status_filter=status_filter,
    )
    return templates.TemplateResponse(
        request,
        "admin/posts.html",
        {
            "user": user,
            "posts": posts,
            "status_filter": status_filter,
            "page_title": "Mis posts" if not is_admin else "Todos los posts",
        },
    )


# ---------------- Crear ----------------
@router.get("/posts/new", response_class=Response)
async def new_post_form(
    request: Request,
    user: EditorOrAdmin,
):
    return templates.TemplateResponse(
        request,
        "admin/post_form.html",
        {
            "user": user,
            "post": None,
            "page_title": "Nuevo post",
            "form_action": "/admin/posts",
            "errors": {},
        },
    )


@router.post("/posts")
async def create_post(
    request: Request,
    db: DBSession,
    user: EditorOrAdmin,
    title: str = Form(...),
    slug: str | None = Form(None),
    excerpt: str | None = Form(None),
    content: str = Form(...),
    cover_image_url: str | None = Form(None),
    is_featured: bool = Form(False),
    action: str = Form("draft"),  # 'draft' | 'publish'
) -> RedirectResponse:
    """Crea un post. `action` decide si queda en borrador o se publica."""
    target_status = PostStatus.PUBLISHED if action == "publish" else PostStatus.DRAFT

    payload = PostCreate(
        title=title.strip(),
        slug=slug.strip() if slug else None,
        excerpt=excerpt.strip() if excerpt else None,
        content=content,
        cover_image_url=cover_image_url.strip() if cover_image_url else None,
        is_featured=is_featured,
        status=target_status,
    )

    db_user = await _resolve_user_or_404(db, user)
    post = await post_service.create_post(db, payload, db_user)
    await post_service.maybe_sync_featured(db, post)

    return RedirectResponse(
        url=f"/admin/posts/{post.id}/edit",
        status_code=status.HTTP_303_SEE_OTHER,
    )


# ---------------- Editar ----------------
@router.get("/posts/{post_id}/edit", response_class=Response)
async def edit_post_form(
    request: Request,
    post_id: uuid.UUID,
    db: DBSession,
    user: EditorOrAdmin,
):
    post = await post_service.get_post_by_id(db, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post no encontrado")
    if user.role != "admin" and post.author_id != user.id:
        raise HTTPException(status_code=403, detail="No puedes editar este post")

    return templates.TemplateResponse(
        request,
        "admin/post_form.html",
        {
            "user": user,
            "post": post,
            "page_title": f"Editar: {post.title}",
            "form_action": f"/admin/posts/{post.id}",
            "errors": {},
        },
    )


@router.post("/posts/{post_id}")
async def update_post(
    post_id: uuid.UUID,
    db: DBSession,
    user: EditorOrAdmin,
    title: str = Form(...),
    slug: str | None = Form(None),
    excerpt: str | None = Form(None),
    content: str = Form(...),
    cover_image_url: str | None = Form(None),
    is_featured: bool = Form(False),
    action: str = Form("draft"),
) -> RedirectResponse:
    post = await post_service.get_post_by_id(db, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post no encontrado")
    if user.role != "admin" and post.author_id != user.id:
        raise HTTPException(status_code=403, detail="No puedes editar este post")

    target_status = PostStatus.PUBLISHED if action == "publish" else PostStatus.DRAFT

    update_payload = PostUpdate(
        title=title.strip(),
        slug=slug.strip() if slug else None,
        excerpt=excerpt.strip() if excerpt else None,
        content=content,
        cover_image_url=cover_image_url.strip() if cover_image_url else None,
        is_featured=is_featured,
        status=target_status,
    )

    post = await post_service.update_post(db, post, update_payload)
    await post_service.maybe_sync_featured(db, post)

    return RedirectResponse(
        url=f"/admin/posts/{post.id}/edit",
        status_code=status.HTTP_303_SEE_OTHER,
    )


# ---------------- Eliminar ----------------
@router.post("/posts/{post_id}/delete")
async def delete_post(
    post_id: uuid.UUID,
    db: DBSession,
    user: EditorOrAdmin,
) -> RedirectResponse:
    post = await post_service.get_post_by_id(db, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post no encontrado")
    if user.role != "admin" and post.author_id != user.id:
        raise HTTPException(status_code=403, detail="No puedes eliminar este post")
    await post_service.delete_post(db, post)
    logger.info("Post {} eliminado por {}", post_id, user.username)
    return RedirectResponse(url="/admin/posts", status_code=status.HTTP_303_SEE_OTHER)
