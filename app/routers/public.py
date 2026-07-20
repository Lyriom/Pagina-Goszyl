"""Localized corporate pages, contact delivery, and SEO endpoints."""

from __future__ import annotations

from html import escape
from urllib.parse import urlsplit

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse, RedirectResponse, Response
from loguru import logger
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from app.config import settings
from app.contact import (
    CONTACT_SENT_COOKIE_NAME,
    CSRF_COOKIE_NAME,
    MAX_CONTACT_BODY_BYTES,
    contact_rate_limiter,
    csrf_matches,
    new_csrf_token,
    parse_submission,
    sent_receipt_matches,
)
from app.i18n import Locale, PageName, ROUTES, localized_context, translate
from app.services.email_service import EmailDeliveryError, send_contact_email
from app.templating import templates

router = APIRouter(tags=["public"])


def _page_context(
    locale: Locale,
    page: PageName,
    title_key: str,
    spanish_title: str,
    description_key: str,
    spanish_description: str,
) -> dict[str, object]:
    context = localized_context(locale, page)
    context.update(
        {
            "canonical_url": f"{settings.APP_URL}{ROUTES[locale][page]}",
            "organization_description": translate(
                locale,
                "meta.organization_description",
                settings.APP_DESCRIPTION,
            ),
            "page_title": translate(locale, title_key, spanish_title),
            "page_description": translate(
                locale,
                description_key,
                spanish_description,
            ),
        }
    )
    return context


def _render_page(
    request: Request,
    template_name: str,
    locale: Locale,
    page: PageName,
    title_key: str,
    spanish_title: str,
    description_key: str,
    spanish_description: str,
    *,
    extra: dict[str, object] | None = None,
    status_code: int = 200,
) -> Response:
    context = _page_context(
        locale,
        page,
        title_key,
        spanish_title,
        description_key,
        spanish_description,
    )
    if extra:
        context.update(extra)
    return templates.TemplateResponse(
        request,
        template_name,
        context,
        status_code=status_code,
    )


def _render_home(request: Request, locale: Locale) -> Response:
    return _render_page(
        request,
        "public/home.html",
        locale,
        "home",
        "meta.home_title",
        f"{settings.APP_NAME} | Producto digital, IA y automatización",
        "meta.home_description",
        settings.APP_DESCRIPTION,
    )


def _render_about(request: Request, locale: Locale) -> Response:
    return _render_page(
        request,
        "public/about.html",
        locale,
        "about",
        "meta.about_title",
        f"Acerca de {settings.APP_NAME}",
        "meta.about_description",
        (
            f"Conoce {settings.APP_NAME} y nuestra forma de combinar producto, diseño "
            "e ingeniería para construir sistemas digitales útiles."
        ),
    )


@router.get("/", response_class=Response)
async def home_es(request: Request) -> Response:
    return _render_home(request, "es")


@router.get("/en", response_class=Response)
async def home_en(request: Request) -> Response:
    return _render_home(request, "en")


@router.get("/acerca", response_class=Response)
async def about_es(request: Request) -> Response:
    return _render_about(request, "es")


@router.get("/en/about", response_class=Response)
async def about_en(request: Request) -> Response:
    return _render_about(request, "en")


def _contact_response(
    request: Request,
    locale: Locale,
    *,
    sent: bool = False,
    form_error: str | None = None,
    form_values: dict[str, str] | None = None,
    status_code: int = 200,
    retry_after: int | None = None,
    clear_sent_receipt: bool = False,
) -> Response:
    csrf_token = new_csrf_token()
    response = _render_page(
        request,
        "public/contact.html",
        locale,
        "contact",
        "meta.contact_title",
        f"Contacto | {settings.APP_NAME}",
        "meta.contact_description",
        (
            f"Cuéntale a {settings.APP_NAME} qué proceso, producto o experiencia digital "
            "quieres construir o mejorar."
        ),
        extra={
            "contact_sent": sent,
            "form_error": form_error,
            "form_values": form_values or {},
            "csrf_token": csrf_token,
        },
        status_code=status_code,
    )
    response.set_cookie(
        CSRF_COOKIE_NAME,
        csrf_token,
        max_age=3600,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        path="/",
    )
    if retry_after is not None:
        response.headers["Retry-After"] = str(retry_after)
    if clear_sent_receipt:
        response.delete_cookie(CONTACT_SENT_COOKIE_NAME, path="/")
    return response


@router.get("/contacto", response_class=Response)
async def contact_es(request: Request, sent: str | None = None) -> Response:
    confirmed = sent_receipt_matches(
        request.cookies.get(CONTACT_SENT_COOKIE_NAME),
        sent,
    )
    return _contact_response(
        request,
        "es",
        sent=confirmed,
        clear_sent_receipt=confirmed,
    )


@router.get("/en/contact", response_class=Response)
async def contact_en(request: Request, sent: str | None = None) -> Response:
    confirmed = sent_receipt_matches(
        request.cookies.get(CONTACT_SENT_COOKIE_NAME),
        sent,
    )
    return _contact_response(
        request,
        "en",
        sent=confirmed,
        clear_sent_receipt=confirmed,
    )


def _same_origin(request: Request) -> bool:
    origin = request.headers.get("origin")
    if not origin:
        return True
    submitted = urlsplit(origin)
    expected = urlsplit(settings.APP_URL)
    return submitted.scheme == expected.scheme and submitted.netloc == expected.netloc


def _client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"


async def _read_limited_body(request: Request) -> bool:
    """Read and cache the request body while enforcing the limit for all encodings."""
    chunks: list[bytes] = []
    total = 0
    async for chunk in request.stream():
        total += len(chunk)
        if total > MAX_CONTACT_BODY_BYTES:
            return False
        chunks.append(chunk)
    request._body = b"".join(chunks)  # Starlette reuses this cache in request.form().
    return True


def _success_redirect(locale: Locale) -> RedirectResponse:
    receipt = new_csrf_token()
    response = RedirectResponse(
        url=f"{ROUTES[locale]['contact']}?sent={receipt}",
        status_code=303,
    )
    response.set_cookie(
        CONTACT_SENT_COOKIE_NAME,
        receipt,
        max_age=120,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        path="/",
    )
    response.delete_cookie(CSRF_COOKIE_NAME, path="/")
    return response


async def _submit_contact(request: Request, locale: Locale) -> Response:
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > MAX_CONTACT_BODY_BYTES:
                raise ValueError
        except ValueError:
            return _contact_response(
                request,
                locale,
                form_error=translate(
                    locale,
                    "contact.validation_error",
                    "Revisa los campos e inténtalo de nuevo.",
                ),
                status_code=413,
            )

    if not await _read_limited_body(request):
        return _contact_response(
            request,
            locale,
            form_error=translate(
                locale,
                "contact.validation_error",
                "Revisa los campos e inténtalo de nuevo.",
            ),
            status_code=413,
        )

    form = await request.form()
    field_names = (
        "name",
        "email",
        "company",
        "message",
        "consent",
        "website",
        "csrf_token",
    )
    values = {name: str(form.get(name, "")) for name in field_names}
    public_values = {
        key: value
        for key, value in values.items()
        if key not in {"csrf_token", "website"}
    }

    if not _same_origin(request) or not csrf_matches(
        request.cookies.get(CSRF_COOKIE_NAME),
        values["csrf_token"],
    ):
        return _contact_response(
            request,
            locale,
            form_error=translate(
                locale,
                "contact.csrf_error",
                "El formulario expiró. Recarga la página e inténtalo de nuevo.",
            ),
            form_values=public_values,
            status_code=403,
        )

    retry_after = contact_rate_limiter.register(_client_key(request))
    if retry_after is not None:
        return _contact_response(
            request,
            locale,
            form_error=translate(
                locale,
                "contact.rate_error",
                "Demasiados intentos. Espera unos minutos antes de volver a intentarlo.",
            ),
            form_values=public_values,
            status_code=429,
            retry_after=retry_after,
        )

    # Honeypot: return the same success flow without sending or revealing detection.
    if values["website"]:
        return _success_redirect(locale)

    try:
        submission = parse_submission(values)
    except ValidationError:
        return _contact_response(
            request,
            locale,
            form_error=translate(
                locale,
                "contact.validation_error",
                "Revisa los campos e inténtalo de nuevo.",
            ),
            form_values=public_values,
            status_code=422,
        )

    try:
        await run_in_threadpool(send_contact_email, submission, locale)
    except EmailDeliveryError as exc:
        logger.error("Contact-form delivery failed: {}", type(exc).__name__)
        return _contact_response(
            request,
            locale,
            form_error=translate(
                locale,
                "contact.delivery_error",
                "No pudimos entregar tu mensaje ahora. Inténtalo nuevamente más tarde.",
            ),
            form_values=public_values,
            status_code=503,
        )

    return _success_redirect(locale)


@router.post("/contacto", response_class=Response)
async def submit_contact_es(request: Request) -> Response:
    return await _submit_contact(request, "es")


@router.post("/en/contact", response_class=Response)
async def submit_contact_en(request: Request) -> Response:
    return await _submit_contact(request, "en")


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
    """Sitemap with bidirectional ES/EN alternates for every public page."""
    entries: list[str] = []
    page_settings: tuple[tuple[PageName, str, str], ...] = (
        ("home", "weekly", "1.0"),
        ("about", "monthly", "0.7"),
        ("contact", "monthly", "0.6"),
    )
    for page, frequency, priority in page_settings:
        spanish_url = f"{settings.APP_URL}{ROUTES['es'][page]}"
        english_url = f"{settings.APP_URL}{ROUTES['en'][page]}"
        alternates = (
            f'<xhtml:link rel="alternate" hreflang="es" href="{escape(spanish_url, quote=True)}"/>'
            f'<xhtml:link rel="alternate" hreflang="en" href="{escape(english_url, quote=True)}"/>'
            f'<xhtml:link rel="alternate" hreflang="x-default" href="{escape(spanish_url, quote=True)}"/>'
        )
        for page_url in (spanish_url, english_url):
            entries.append(
                f"<url><loc>{escape(page_url)}</loc>{alternates}"
                f"<changefreq>{frequency}</changefreq><priority>{priority}</priority></url>"
            )

    body = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml">'
        + "".join(entries)
        + "</urlset>"
    )
    return Response(content=body, media_type="application/xml")


@router.get("/healthz", include_in_schema=False)
async def healthz() -> dict[str, str]:
    return {"status": "ok"}
