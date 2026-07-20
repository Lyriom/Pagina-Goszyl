"""Rutas públicas: landing, acerca, blog y SEO (sitemap/robots)."""

from __future__ import annotations

from datetime import datetime
from math import ceil

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import PlainTextResponse, Response

from app.config import settings
from app.database import DBSession
from app.services import post_service
from app.templating import templates

router = APIRouter(tags=["public"])


@router.get("/", response_class=Response)
async def home(request: Request):
    """Landing corporativa con servicios y proyectos."""
    return templates.TemplateResponse(
        request,
        "public/home.html",
        {
            "page_title": f"{settings.APP_NAME} | Producto digital, IA y automatización",
            "page_description": settings.APP_DESCRIPTION,
        },
    )


@router.get("/acerca", response_class=Response)
async def about(request: Request):
    """Página 'Acerca de'."""
    return templates.TemplateResponse(
        request,
        "public/about.html",
        {
            "page_title": f"Acerca de {settings.APP_NAME}",
            "page_description": (
                f"Conoce a {settings.APP_NAME}, una empresa de tecnología constituida "
                f"en {settings.COMPANY_JURISDICTION}."
            ),
        },
    )


@router.get("/blog", response_class=Response)
async def blog_index(
    request: Request,
    db: DBSession,
    page: int = Query(1, ge=1),
):
    """Listado paginado de posts publicados (10 por página)."""
    page_size = 10
    posts, total = (
        ([], 0)
        if settings.DEV_PREVIEW_MODE
        else await post_service.list_published_posts(db, page=page, page_size=page_size)
    )
    total_pages = max(ceil(total / page_size), 1)

    return templates.TemplateResponse(
        request,
        "public/blog.html",
        {
            "posts": posts,
            "page": page,
            "total_pages": total_pages,
            "total": total,
            "canonical_url": (
                f"{settings.APP_URL}/blog?page={page}"
                if page > 1
                else f"{settings.APP_URL}/blog"
            ),
            "page_title": f"Blog | {settings.APP_NAME}",
            "page_description": (
                f"Artículos de {settings.APP_NAME} sobre producto digital, inteligencia "
                "artificial, automatización y datos."
            ),
        },
    )


@router.get("/blog/{slug}", response_class=Response)
async def blog_post(
    request: Request,
    slug: str,
    db: DBSession,
):
    """Detalle de un post publicado, con SEO y schema.org."""
    post = None if settings.DEV_PREVIEW_MODE else await post_service.get_post_by_slug(db, slug)
    if post is None or not post.is_published:
        raise HTTPException(status_code=404, detail="Post no encontrado")

    canonical = f"{settings.APP_URL}/blog/{post.slug}"
    return templates.TemplateResponse(
        request,
        "public/post.html",
        {
            "post": post,
            "canonical_url": canonical,
            "page_title": f"{post.title} | {settings.APP_NAME}",
            "page_description": post.excerpt or settings.APP_DESCRIPTION,
            "og_image": post.cover_image_url,
            "og_type": "article",
        },
    )


# ---------------- SEO ----------------
@router.get("/robots.txt", response_class=PlainTextResponse, include_in_schema=False)
async def robots_txt() -> str:
    return (
        "User-agent: *\n"
        "Allow: /\n"
        f"Sitemap: {settings.APP_URL}/sitemap.xml\n"
    )


@router.get("/sitemap.xml", include_in_schema=False)
async def sitemap_xml(db: DBSession) -> Response:
    """Sitemap dinámico construido a partir de los posts publicados."""
    posts, _ = (
        ([], 0)
        if settings.DEV_PREVIEW_MODE
        else await post_service.list_published_posts(db, page=1, page_size=1000)
    )
    now_iso = datetime.utcnow().date().isoformat()

    urls: list[str] = [
        f"<url><loc>{settings.APP_URL}/</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>",
        f"<url><loc>{settings.APP_URL}/acerca</loc><changefreq>monthly</changefreq><priority>0.6</priority></url>",
        f"<url><loc>{settings.APP_URL}/blog</loc><changefreq>daily</changefreq><priority>0.8</priority></url>",
    ]
    for post in posts:
        last = (post.updated_at or post.created_at).date().isoformat() if post.updated_at else now_iso
        urls.append(
            f"<url><loc>{settings.APP_URL}/blog/{post.slug}</loc>"
            f"<lastmod>{last}</lastmod><priority>0.7</priority></url>"
        )

    body = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(urls)
        + "</urlset>"
    )
    return Response(content=body, media_type="application/xml")


@router.get("/healthz", include_in_schema=False)
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


# Render mínimo de error 404 (lo gestiona main mediante el exception handler).
@router.get("/_404", include_in_schema=False)
async def not_found_page(request: Request) -> Response:
    return templates.TemplateResponse(
        request,
        "public/404.html",
        {"page_title": "No encontrado"},
        status_code=status.HTTP_404_NOT_FOUND,
    )
