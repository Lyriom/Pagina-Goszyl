"""Conexión async a PostgreSQL vía SQLAlchemy 2.0.

Expone:
- `engine`: AsyncEngine compartido del proceso.
- `AsyncSessionLocal`: factory de sesiones.
- `Base`: clase base declarativa para los modelos.
- `get_session`: dependencia FastAPI que cede una sesión por solicitud.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """Clase base para los modelos ORM del blog."""


engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
    class_=AsyncSession,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Cede una sesión asíncrona; hace commit al salir si no hubo excepciones."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


DBSession = Annotated[AsyncSession, Depends(get_session)]
