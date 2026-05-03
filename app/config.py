"""Configuracion central de la aplicacion.

Carga variables de entorno con Pydantic Settings y las expone como
un objeto inmutable (`settings`) para inyectar via FastAPI Depends.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuracion tipada del Sistema A."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- Aplicacion ---
    APP_URL: str = "http://localhost:8000"
    APP_NAME: str = "Gozsyl"
    APP_DESCRIPTION: str = "Tecnologia y soluciones digitales"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    LOG_LEVEL: str = "INFO"

    # --- Sesion ---
    SECRET_KEY: str = Field(min_length=16)
    SESSION_COOKIE_NAME: str = "sistema_a_session"
    SESSION_MAX_AGE: int = 86_400  # 24h

    # --- Base de datos ---
    DATABASE_URL: str

    # --- Keycloak ---
    KEYCLOAK_URL: str
    KEYCLOAK_REALM: str
    KEYCLOAK_CLIENT_ID: str
    KEYCLOAK_CLIENT_SECRET: str
    KEYCLOAK_REDIRECT_URI: str
    KEYCLOAK_POST_LOGOUT_URI: str = ""

    # --- Vault ---
    VAULT_URL: str
    VAULT_TOKEN: str
    VAULT_TRANSIT_KEY: str = "featured-content-key"
    VAULT_TRANSIT_MOUNT: str = "transit"

    # --- Sistema B ---
    SISTEMA_B_URL: str
    SISTEMA_B_API_KEY: str
    SISTEMA_B_TIMEOUT: float = 10.0

    # --- Uploads ---
    MAX_UPLOAD_SIZE_MB: int = 5
    ALLOWED_IMAGE_TYPES: str = "image/jpeg,image/png,image/webp"

    # ----- Helpers -----
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def allowed_image_types_set(self) -> set[str]:
        return {t.strip() for t in self.ALLOWED_IMAGE_TYPES.split(",") if t.strip()}

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @field_validator("KEYCLOAK_URL", "VAULT_URL", "SISTEMA_B_URL", "APP_URL")
    @classmethod
    def _strip_trailing_slash(cls, v: str) -> str:
        return v.rstrip("/")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Devuelve la instancia singleton de Settings (cacheada)."""
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
