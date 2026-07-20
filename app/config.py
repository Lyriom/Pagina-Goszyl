"""Configuración central de la aplicación.

Carga variables de entorno con Pydantic Settings y las expone como
un objeto inmutable (`settings`) para inyectar vía FastAPI Depends.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
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
    # La marca no es configurable: evita que variables heredadas restauren
    # accidentalmente una grafía incorrecta.
    APP_NAME: str = "Gozsyl"
    APP_DESCRIPTION: str = (
        "Consultoría de producto digital, automatización e inteligencia artificial "
        "para empresas que quieren crecer con tecnología."
    )
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    LOG_LEVEL: str = "INFO"

    # --- Entrega de formularios ---
    CONTACT_RECIPIENT_EMAIL: str = "jriera@gozsyl.cloud"
    SMTP_HOST: str | None = None
    SMTP_PORT: int = Field(default=587, ge=1, le=65_535)
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: SecretStr | None = None
    SMTP_FROM_EMAIL: str = "jriera@gozsyl.cloud"
    SMTP_SECURITY: Literal["starttls", "ssl", "none"] = "starttls"
    SMTP_TIMEOUT_SECONDS: int = Field(default=10, ge=1, le=60)

    # ----- Helpers -----
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @field_validator("APP_NAME", mode="before")
    @classmethod
    def _canonicalize_app_name(cls, _value: object) -> str:
        return "Gozsyl"

    @field_validator("CONTACT_RECIPIENT_EMAIL", mode="before")
    @classmethod
    def _canonicalize_contact_recipient(cls, _value: object) -> str:
        return "jriera@gozsyl.cloud"

    @field_validator("APP_URL")
    @classmethod
    def _strip_trailing_slash(cls, v: str) -> str:
        return v.rstrip("/")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Devuelve la instancia singleton de Settings (cacheada)."""
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
