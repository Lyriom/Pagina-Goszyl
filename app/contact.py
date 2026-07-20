"""Validation and abuse controls for the public contact form."""

from __future__ import annotations

import hmac
import re
import secrets
import threading
import time
from collections import defaultdict, deque
from collections.abc import Mapping
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

CSRF_COOKIE_NAME = "gozsyl_contact_csrf"
CONTACT_SENT_COOKIE_NAME = "gozsyl_contact_sent"
MAX_CONTACT_BODY_BYTES = 16_384

_DISALLOWED_CONTROLS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class ContactSubmission(BaseModel):
    """Validated visitor message. Recipient fields never come from the browser."""

    name: str = Field(min_length=2, max_length=80)
    email: EmailStr
    company: str = Field(default="", max_length=100)
    message: str = Field(min_length=20, max_length=3000)
    consent: Literal["accepted"]
    website: str = Field(default="", max_length=200)
    csrf_token: str = Field(min_length=20, max_length=128)

    @field_validator("name", "company", "message", "website", "csrf_token", mode="before")
    @classmethod
    def _strip_strings(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("name", "company")
    @classmethod
    def _reject_controls_in_single_line_fields(cls, value: str) -> str:
        if "\r" in value or "\n" in value or _DISALLOWED_CONTROLS.search(value):
            raise ValueError("invalid control character")
        return value

    @field_validator("message")
    @classmethod
    def _reject_controls_in_message(cls, value: str) -> str:
        if _DISALLOWED_CONTROLS.search(value):
            raise ValueError("invalid control character")
        return value


def parse_submission(values: Mapping[str, object]) -> ContactSubmission:
    return ContactSubmission.model_validate(values)


def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def csrf_matches(cookie_token: str | None, form_token: str | None) -> bool:
    if not cookie_token or not form_token:
        return False
    return hmac.compare_digest(cookie_token, form_token)


def sent_receipt_matches(cookie_token: str | None, query_token: str | None) -> bool:
    """Validate the one-time receipt used after a successful SMTP handoff."""
    if not cookie_token or not query_token:
        return False
    return hmac.compare_digest(cookie_token, query_token)


class ContactRateLimiter:
    """Small per-process safety net; the reverse proxy remains the primary limiter."""

    def __init__(self, limit: int = 5, window_seconds: int = 900) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._attempts: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def register(self, key: str) -> int | None:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            attempts = self._attempts[key]
            while attempts and attempts[0] <= cutoff:
                attempts.popleft()
            if len(attempts) >= self.limit:
                return max(1, int(self.window_seconds - (now - attempts[0])))
            attempts.append(now)
        return None


contact_rate_limiter = ContactRateLimiter()
