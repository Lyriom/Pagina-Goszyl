"""Schemas Pydantic relacionados a usuarios."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserPublic(BaseModel):
    """Representacion publica de un usuario."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    email: EmailStr
    full_name: str | None = None
    role: str
    created_at: datetime
    last_login_at: datetime | None = None


class SessionUser(BaseModel):
    """Usuario almacenado en la sesion server-side (cookie firmada)."""

    id: uuid.UUID
    keycloak_id: str
    username: str
    email: EmailStr
    full_name: str | None = None
    role: str
    roles: list[str] = []  # roles crudos del JWT (incluye client/realm roles)

    def has_any_role(self, *roles: str) -> bool:
        return any(r in self.roles or r == self.role for r in roles)
