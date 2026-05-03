"""Capa de servicio para articulos (consultas y mutaciones).

Mantiene los routers delgados y centraliza:
- Generacion / unicidad de slug.
- Transiciones de estado (draft -> published, published_at).
- Renderizado seguro de Markdown -> HTML (bleach + markdown).
- Disparo de la sincronizacion cifrada hacia Sistema B.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import bleach
import markdown as md_lib
from loguru import logger
from slugify import slugify
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.post import Post, PostStatus
from app.models.user import User
from app.schemas.post import PostCreate, PostUpdate
from app.services.sistema_b_client import sistema_b_client

# ----- Markdown sanitizado (whitelist explicita) -----
_ALLOWED_TAGS = {
    "p", "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li", "blockquote", "pre", "code",
    "strong", "em", "a", "img", "br", "hr",
    "table", "thead", "tbody", "tr", "th", "td",
    "span", "div",
}
_ALLOWED_ATTRS = {
    "a": ["href", "title", "rel", "target"],
    "img": ["src", "alt", "title", "loading"],
    "code": ["class"],
    "span": ["class"],
    "div": ["class"],
}
_ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


def render_markdown_safe(content: str) -> str:
    """Renderiza Markdown a HTML pasandolo por bleach con whitelist."""
    raw_html = md_lib.markdown(
        content,
        extensions=["fenced_code", "tables", "toc", "sane_lists"],
        output_format="html",
    )
    cleaned = bleach.clean(
        raw_html,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRS,
        protocols=_ALLOWED_PROTOCOLS,
        strip=True,
    )
    return bleach.linkify(cleaned, skip_tags=["pre", "code"])


# ===================== Consultas =====================
async def get_post_by_slug(db: AsyncSession, slug: str) -> Post | None:
    stmt = (
        select(Post)
        .options(selectinload(Post.author))
        .where(Post.slug == slug)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def get_post_by_id(db: AsyncSession, post_id: uuid.UUID) -> Post | None:
    stmt = (
        select(Post)
        .options(selectinload(Post.author))
        .where(Post.id == post_id)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def list_published_posts(
    db: AsyncSession, *, page: int = 1, page_size: int = 10
) -> tuple[list[Post], int]:
    """Devuelve (posts, total) de los publicados, ordenados por fecha desc."""
    page = max(page, 1)
    offset = (page - 1) * page_size

    base = select(Post).where(Post.status == PostStatus.PUBLISHED.value)

    total = (
        await db.execute(select(func.count()).select_from(base.subquery()))
    ).scalar_one()

    stmt = (
        base.options(selectinload(Post.author))
        .order_by(Post.published_at.desc().nullslast(), Post.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    posts = list((await db.execute(stmt)).scalars().all())
    return posts, total


async def list_recent_published(db: AsyncSession, limit: int = 3) -> list[Post]:
    stmt = (
        select(Post)
        .options(selectinload(Post.author))
        .where(Post.status == PostStatus.PUBLISHED.value)
        .order_by(Post.published_at.desc().nullslast(), Post.created_at.desc())
        .limit(limit)
    )
    return list((await db.execute(stmt)).scalars().all())


async def list_admin_posts(
    db: AsyncSession,
    *,
    author_id: uuid.UUID | None = None,
    status_filter: str | None = None,
) -> list[Post]:
    """Listado para zona admin: todos si admin, propios si editor."""
    stmt = select(Post).options(selectinload(Post.author))
    if author_id is not None:
        stmt = stmt.where(Post.author_id == author_id)
    if status_filter:
        stmt = stmt.where(Post.status == status_filter)
    stmt = stmt.order_by(Post.updated_at.desc())
    return list((await db.execute(stmt)).scalars().all())


async def count_posts_by_status(db: AsyncSession) -> dict[str, int]:
    stmt = select(Post.status, func.count()).group_by(Post.status)
    rows = (await db.execute(stmt)).all()
    counts = {PostStatus.DRAFT.value: 0, PostStatus.PUBLISHED.value: 0}
    for status_value, n in rows:
        counts[status_value] = n
    return counts


# ===================== Mutaciones =====================
async def _ensure_unique_slug(
    db: AsyncSession, base_slug: str, *, exclude_id: uuid.UUID | None = None
) -> str:
    """Garantiza unicidad agregando -2, -3, ... si hace falta."""
    candidate = base_slug
    suffix = 2
    while True:
        stmt = select(Post.id).where(Post.slug == candidate)
        if exclude_id:
            stmt = stmt.where(Post.id != exclude_id)
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing is None:
            return candidate
        candidate = f"{base_slug}-{suffix}"
        suffix += 1


async def create_post(db: AsyncSession, data: PostCreate, author: User) -> Post:
    slug_base = data.slug or slugify(data.title, max_length=255)
    slug = await _ensure_unique_slug(db, slug_base)

    now = datetime.now(timezone.utc)
    post = Post(
        title=data.title,
        slug=slug,
        excerpt=data.excerpt,
        content=data.content,
        cover_image_url=str(data.cover_image_url) if data.cover_image_url else None,
        author_id=author.id,
        status=data.status.value,
        is_featured=data.is_featured,
        published_at=now if data.status == PostStatus.PUBLISHED else None,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post, attribute_names=["author"])
    logger.info("Post creado: id={} slug={} status={}", post.id, post.slug, post.status)
    return post


async def update_post(
    db: AsyncSession,
    post: Post,
    data: PostUpdate,
) -> Post:
    """Aplica cambios y maneja la transicion a `published`."""
    was_published = post.is_published

    if data.title is not None:
        post.title = data.title
    if data.slug is not None:
        post.slug = await _ensure_unique_slug(db, data.slug, exclude_id=post.id)
    if data.excerpt is not None:
        post.excerpt = data.excerpt
    if data.content is not None:
        post.content = data.content
    if data.cover_image_url is not None:
        post.cover_image_url = str(data.cover_image_url)
    if data.is_featured is not None:
        post.is_featured = data.is_featured
    if data.status is not None and data.status.value != post.status:
        post.status = data.status.value
        if data.status == PostStatus.PUBLISHED and not was_published:
            post.published_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(post, attribute_names=["author"])
    logger.info("Post actualizado: id={} slug={}", post.id, post.slug)
    return post


async def delete_post(db: AsyncSession, post: Post) -> None:
    await db.delete(post)
    await db.commit()
    logger.info("Post eliminado: id={}", post.id)


async def maybe_sync_featured(db: AsyncSession, post: Post) -> None:
    """Si el post es destacado y esta publicado, lo manda al Sistema B.

    No bloquea el flujo del editor: errores se loggean y se persisten
    en `featured_sync_log` via `sistema_b_client`.
    """
    if not (post.is_featured and post.is_published):
        return
    try:
        result = await sistema_b_client.send_featured_post(post, db)
        if not result.success:
            logger.warning(
                "Sync featured a Sistema B fallo (post={} status={})",
                post.id,
                result.status_code,
            )
    except Exception as e:  # ultima red de seguridad
        logger.exception("Excepcion inesperada al sincronizar con Sistema B: {}", e)
