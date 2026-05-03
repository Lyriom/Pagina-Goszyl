"""Modelo User - sincronizado con identidades de Keycloak."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.post import Post


class UserRole(StrEnum):
    """Roles soportados, replicados desde Keycloak."""

    USER = "user"
    EDITOR = "editor"
    ADMIN = "admin"


class User(Base):
    """Usuario local, espejo del usuario federado en Keycloak.

    `keycloak_id` corresponde al `sub` del JWT (UUID de Keycloak).
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    keycloak_id: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    username: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default=UserRole.USER.value
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    posts: Mapped[list["Post"]] = relationship(
        "Post",
        back_populates="author",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def has_role(self, *roles: str) -> bool:
        """True si el rol del usuario esta en la lista pasada."""
        return self.role in roles

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.username} ({self.role})>"
