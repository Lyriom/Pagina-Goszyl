"""initial schema (users, posts, featured_sync_log)

Revision ID: 0001
Revises:
Create Date: 2026-05-02

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ----- users -----
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("keycloak_id", sa.String(length=64), nullable=False),
        sa.Column("username", sa.String(length=150), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="user"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint("uq_users_keycloak_id", "users", ["keycloak_id"])
    op.create_index("ix_users_keycloak_id", "users", ["keycloak_id"])
    op.create_index("ix_users_email", "users", ["email"])

    # ----- posts -----
    op.create_table(
        "posts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("cover_image_url", sa.Text(), nullable=True),
        sa.Column(
            "author_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="draft"
        ),
        sa.Column(
            "is_featured",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_unique_constraint("uq_posts_slug", "posts", ["slug"])
    op.create_index("ix_posts_slug", "posts", ["slug"])
    op.create_index("ix_posts_author_id", "posts", ["author_id"])
    op.create_index("ix_posts_status", "posts", ["status"])
    op.create_index("ix_posts_is_featured", "posts", ["is_featured"])
    op.create_index("ix_posts_published_at", "posts", ["published_at"])

    # ----- featured_sync_log -----
    op.create_table(
        "featured_sync_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "post_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("posts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("request_payload_hash", sa.String(length=128), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=True),
        sa.Column("response_message", sa.Text(), nullable=True),
        sa.Column(
            "sent_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "success", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.create_index("ix_featured_sync_log_post_id", "featured_sync_log", ["post_id"])


def downgrade() -> None:
    op.drop_index("ix_featured_sync_log_post_id", table_name="featured_sync_log")
    op.drop_table("featured_sync_log")

    op.drop_index("ix_posts_published_at", table_name="posts")
    op.drop_index("ix_posts_is_featured", table_name="posts")
    op.drop_index("ix_posts_status", table_name="posts")
    op.drop_index("ix_posts_author_id", table_name="posts")
    op.drop_index("ix_posts_slug", table_name="posts")
    op.drop_constraint("uq_posts_slug", "posts", type_="unique")
    op.drop_table("posts")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_keycloak_id", table_name="users")
    op.drop_constraint("uq_users_keycloak_id", "users", type_="unique")
    op.drop_table("users")
