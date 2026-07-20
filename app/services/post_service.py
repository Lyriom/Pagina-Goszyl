"""Consultas de lectura y renderizado seguro para el blog público."""

from __future__ import annotations

import bleach
import markdown as md_lib
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.post import Post, PostStatus

_ALLOWED_TAGS = {
    "p",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "ul",
    "ol",
    "li",
    "blockquote",
    "pre",
    "code",
    "strong",
    "em",
    "a",
    "img",
    "br",
    "hr",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "span",
    "div",
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
    """Convierte Markdown en HTML y elimina etiquetas o atributos peligrosos."""
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


async def get_post_by_slug(db: AsyncSession, slug: str) -> Post | None:
    stmt = (
        select(Post)
        .options(selectinload(Post.author))
        .where(Post.slug == slug)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def list_published_posts(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 10,
) -> tuple[list[Post], int]:
    """Devuelve los artículos publicados y su total para la paginación."""
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
    return list((await db.execute(stmt)).scalars().all()), total
