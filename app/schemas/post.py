"""Schemas Pydantic relacionados a articulos del blog."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator
from slugify import slugify

from app.models.post import PostStatus

TitleStr = Annotated[str, Field(min_length=3, max_length=255)]
SlugStr = Annotated[str, Field(min_length=3, max_length=255, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")]


class PostBase(BaseModel):
    """Campos comunes a creacion y actualizacion."""

    title: TitleStr
    slug: SlugStr | None = None
    excerpt: str | None = Field(default=None, max_length=500)
    content: str = Field(min_length=1)
    cover_image_url: HttpUrl | None = None
    is_featured: bool = False

    @field_validator("slug", mode="before")
    @classmethod
    def _normalize_slug(cls, v: str | None) -> str | None:
        if not v:
            return None
        return slugify(v, max_length=255)


class PostCreate(PostBase):
    """Datos requeridos para crear un post."""

    status: PostStatus = PostStatus.DRAFT


class PostUpdate(BaseModel):
    """Datos para actualizar un post (todos opcionales)."""

    title: TitleStr | None = None
    slug: SlugStr | None = None
    excerpt: str | None = Field(default=None, max_length=500)
    content: str | None = None
    cover_image_url: HttpUrl | None = None
    is_featured: bool | None = None
    status: PostStatus | None = None

    @field_validator("slug", mode="before")
    @classmethod
    def _normalize_slug(cls, v: str | None) -> str | None:
        if not v:
            return None
        return slugify(v, max_length=255)


class PostAuthor(BaseModel):
    """Autor reducido para listados publicos."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    full_name: str | None = None


class PostListItem(BaseModel):
    """Item compacto usado en listados (cards de blog, dashboard, tabla admin)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    slug: str
    excerpt: str | None
    cover_image_url: str | None
    status: str
    is_featured: bool
    published_at: datetime | None
    created_at: datetime
    author: PostAuthor


class PostPublic(BaseModel):
    """Detalle completo de un post publicado."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    slug: str
    excerpt: str | None
    content: str
    cover_image_url: str | None
    status: str
    is_featured: bool
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime
    author: PostAuthor
