"""Modelo FeaturedSyncLog - auditoria de envios cifrados al Sistema B."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.post import Post


class FeaturedSyncLog(Base):
    """Registro de cada intento de sincronizacion cifrada A -> B.

    Solo guarda hashes y metadatos. El payload original (titulo, slug, etc)
    no se persiste aqui — se reconstruye desde el `Post` enlazado.
    """

    __tablename__ = "featured_sync_log"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    post_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    request_payload_hash: Mapped[str] = mapped_column(
        String(128), nullable=False
    )
    response_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    post: Mapped["Post"] = relationship("Post", back_populates="sync_logs")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<FeaturedSyncLog post={self.post_id} ok={self.success}>"
