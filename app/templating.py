"""Configuración compartida de Jinja2 (autoescape activo).

Se centraliza aquí para que los routers solo importen `templates`
y para registrar globals comunes (settings, helpers de URL, etc).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi.templating import Jinja2Templates
from markupsafe import Markup

from app.config import settings
from app.services.post_service import render_markdown_safe

TEMPLATES_DIR = Path(__file__).parent / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _markdown_filter(value: str | None) -> Markup:
    if not value:
        return Markup("")
    return Markup(render_markdown_safe(value))


SPANISH_MONTHS = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)


def _format_date(value: datetime | None, fmt: str | None = None) -> str:
    if value is None:
        return ""
    if fmt:
        return value.strftime(fmt)
    return f"{value.day} de {SPANISH_MONTHS[value.month - 1]} de {value.year}"


# --- Filtros / globals ---
templates.env.filters["markdown"] = _markdown_filter
templates.env.filters["format_date"] = _format_date

templates.env.globals["app_name"] = settings.APP_NAME
templates.env.globals["app_url"] = settings.APP_URL
templates.env.globals["app_description"] = settings.APP_DESCRIPTION
templates.env.globals["contact_email"] = settings.CONTACT_EMAIL
templates.env.globals["company_jurisdiction"] = settings.COMPANY_JURISDICTION
templates.env.globals["current_year"] = datetime.now().year
