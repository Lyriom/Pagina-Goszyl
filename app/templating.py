"""Configuración compartida de Jinja2 (autoescape activo).

Se centraliza aquí para que los routers solo importen `templates`
y para registrar globals comunes (settings, helpers de URL, etc).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi.templating import Jinja2Templates
from app.config import settings

TEMPLATES_DIR = Path(__file__).parent / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# --- Globals ---
templates.env.globals["app_name"] = settings.APP_NAME
templates.env.globals["app_url"] = settings.APP_URL
templates.env.globals["app_description"] = settings.APP_DESCRIPTION
templates.env.globals["contact_email"] = settings.CONTACT_EMAIL
templates.env.globals["company_jurisdiction"] = settings.COMPANY_JURISDICTION
templates.env.globals["current_year"] = datetime.now().year
