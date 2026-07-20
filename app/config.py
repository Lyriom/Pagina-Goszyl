"""Configuración central de la aplicación.

Carga variables de entorno con Pydantic Settings y las expone como
un objeto inmutable (`settings`) para inyectar vía FastAPI Depends.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración tipada de Gozsyl."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- Aplicación ---
    APP_URL: str = "http://localhost:8000"
    APP_NAME: str = "Gozsyl"
    APP_DESCRIPTION: str = (
        "Consultoría de producto digital, automatización e inteligencia artificial "
        "para empresas que quieren crecer con tecnología."
    )
    CONTACT_EMAIL: str = "hola@gozsyl.com"
    COMPANY_JURISDICTION: str = "Delaware, Estados Unidos"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEV_PREVIEW_MODE: bool = False
    LOG_LEVEL: str = "INFO"

    # --- Base de datos ---
    DATABASE_URL: str

    # ----- Helpers -----
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @field_validator("APP_URL")
    @classmethod
    def _strip_trailing_slash(cls, v: str) -> str:
        return v.rstrip("/")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Devuelve la instancia singleton de Settings (cacheada)."""
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
