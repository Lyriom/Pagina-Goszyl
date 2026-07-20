"""Rutas públicas: landing, acerca y SEO (sitemap/robots)."""

from __future__ import annotations

from fastapi import APIRouter, Request, status
from fastapi.responses import PlainTextResponse, Response

from app.config import settings
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


# ---------------- SEO ----------------
@router.get("/robots.txt", response_class=PlainTextResponse, include_in_schema=False)
async def robots_txt() -> str:
    return (
        "User-agent: *\n"
        "Allow: /\n"
        f"Sitemap: {settings.APP_URL}/sitemap.xml\n"
    )


@router.get("/sitemap.xml", include_in_schema=False)
async def sitemap_xml() -> Response:
    """Sitemap de las páginas públicas de la web corporativa."""
    urls: list[str] = [
        f"<url><loc>{settings.APP_URL}/</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>",
        f"<url><loc>{settings.APP_URL}/acerca</loc><changefreq>monthly</changefreq><priority>0.6</priority></url>",
    ]

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
