"""Punto de entrada de la web corporativa de Gozsyl.

- Crea la aplicación FastAPI.
- Registra CSP y cabeceras de seguridad.
- Monta las rutas públicas y los archivos estáticos.
- Define páginas de error que respetan HTML y JSON.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from loguru import logger
from starlette.exceptions import HTTPException

from app.config import settings
from app.logging_setup import configure_logging
from app.routers import public
from app.templating import templates

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Hooks de arranque/parada."""
    configure_logging()
    logger.info(
        "Gozsyl iniciado: env={} url={}",
        settings.ENVIRONMENT,
        settings.APP_URL,
    )
    yield
    logger.info("Gozsyl apagándose...")


app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version="0.1.0",
    docs_url="/api/docs" if not settings.is_production else None,
    redoc_url=None,
    openapi_url="/api/openapi.json" if not settings.is_production else None,
    lifespan=lifespan,
)

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Inyecta cabeceras de seguridad básicas (XSS, clickjacking y MIME)."""
    response: Response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Permissions-Policy",
        "geolocation=(), microphone=(), camera=()",
    )
    if settings.is_production:
        response.headers.setdefault(
            "Strict-Transport-Security",
            "max-age=31536000; includeSubDomains",
        )
    # CSP compatible con las fuentes y la medición consentida declaradas en base.html.
    response.headers.setdefault(
        "Content-Security-Policy",
        (
            "default-src 'self'; "
            "img-src 'self' data: https:; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com data:; "
            "script-src 'self' 'unsafe-inline' https://www.googletagmanager.com; "
            "connect-src 'self' https://www.google-analytics.com https://*.google-analytics.com "
            "https://www.googletagmanager.com; "
            "frame-src 'none'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        ),
    )
    return response


# ---------------- Static files ----------------
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ---------------- Routers ----------------
app.include_router(public.router)


# ---------------- Exception handlers ----------------
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Convierte errores HTTP en HTML cuando el navegador lo solicita."""
    accepts_html = "text/html" in request.headers.get("accept", "")
    if not accepts_html:
        # La API JSON usa el comportamiento predeterminado.
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=exc.headers,
        )

    if exc.status_code == status.HTTP_404_NOT_FOUND:
        return templates.TemplateResponse(
            request,
            "public/404.html",
            {
                "page_title": "Página no encontrada",
                "error_code": 404,
                "error_title": "Página no encontrada",
                "error_message": (
                    "La página que buscas no existe, cambió de dirección o ya no está disponible."
                ),
            },
            status_code=404,
        )

    if exc.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN):
        return templates.TemplateResponse(
            request,
            "public/404.html",  # reusamos la misma vista
            {
                "page_title": "Acceso restringido",
                "error_code": exc.status_code,
                "error_title": "Acceso restringido",
                "error_message": (
                    "No tienes permiso para ver esta página."
                ),
            },
            status_code=exc.status_code,
        )

    return templates.TemplateResponse(
        request,
        "public/404.html",
        {
            "page_title": "No pudimos completar la solicitud",
            "error_code": exc.status_code,
            "error_title": "No pudimos completar la solicitud",
            "error_message": "Inténtalo de nuevo o escríbenos si el problema continúa.",
        },
        status_code=exc.status_code,
    )
