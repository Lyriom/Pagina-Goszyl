"""Punto de entrada de Sistema A.

- Crea la app FastAPI.
- Registra middlewares (sesion firmada, CSP/security headers).
- Monta routers (publico, auth, admin) y archivos estaticos.
- Define handlers de excepciones (404 / 401 / 403) que respetan HTML.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.exceptions import HTTPException
from fastapi.responses import FileResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from loguru import logger
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.logging_setup import configure_logging
from app.routers import admin, auth, public
from app.templating import templates

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Hooks de arranque/parada."""
    configure_logging()
    logger.info(
        "Sistema A iniciado: env={} url={}",
        settings.ENVIRONMENT,
        settings.APP_URL,
    )
    yield
    logger.info("Sistema A apagandose...")


app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version="0.1.0",
    docs_url="/api/docs" if not settings.is_production else None,
    redoc_url=None,
    openapi_url="/api/openapi.json" if not settings.is_production else None,
    lifespan=lifespan,
)

# ---------------- Middlewares ----------------
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie=settings.SESSION_COOKIE_NAME,
    max_age=settings.SESSION_MAX_AGE,
    same_site="lax",
    https_only=settings.is_production,
)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Inyecta cabeceras de seguridad basicas (XSS, clickjacking, MIME)."""
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
    # CSP relajado para permitir Tailwind / HTMX / Alpine via CDN.
    response.headers.setdefault(
        "Content-Security-Policy",
        (
            "default-src 'self'; "
            "img-src 'self' data: https:; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com data:; "
            "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://unpkg.com; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self';"
        ),
    )
    return response


# ---------------- Static files ----------------
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ---------------- Archivos raiz ----------------
@app.get("/ads.txt", include_in_schema=False)
async def ads_txt():
    return FileResponse(str(STATIC_DIR / "ads.txt"), media_type="text/plain")


# ---------------- Routers ----------------
app.include_router(public.router)
app.include_router(auth.router)
app.include_router(admin.router)


# ---------------- Exception handlers ----------------
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Convierte 401/403/404 en paginas HTML cuando aplica.

    El 307 con header Location lo usamos como atajo de "redirect"
    desde dependencias (`require_login`) — lo respetamos tal cual.
    """
    if exc.status_code == status.HTTP_307_TEMPORARY_REDIRECT and "Location" in (
        exc.headers or {}
    ):
        return RedirectResponse(
            url=exc.headers["Location"],
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )

    accepts_html = "text/html" in request.headers.get("accept", "")
    if not accepts_html:
        # API JSON usa el comportamiento por defecto.
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
            {"user": request.session.get("user"), "page_title": "No encontrado"},
            status_code=404,
        )

    if exc.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN):
        return templates.TemplateResponse(
            request,
            "public/404.html",  # reusamos la misma vista
            {
                "user": request.session.get("user"),
                "page_title": "Acceso restringido",
            },
            status_code=exc.status_code,
        )

    return templates.TemplateResponse(
        request,
        "public/404.html",
        {"user": request.session.get("user"), "page_title": "Error"},
        status_code=exc.status_code,
    )
