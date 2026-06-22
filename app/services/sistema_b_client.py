"""Cliente HTTP hacia Sistema B (comparador de cuotas).

Cuando un post se marca como `featured` y se publica, este servicio:
  1. Construye el plaintext (title, excerpt, content_html, slug) que el
     Sistema B espera para mostrarlo (`FeaturedPlaintext`).
  2. Lo serializa a JSON y lo cifra con Vault Transit.
  3. POST a `{SISTEMA_B_URL}/api/internal/featured-content` con el body
     `{"post_id": "<uuid>", "ciphertext": "vault:v1:..."}` y
     `Authorization: Bearer ...`.
  4. Persiste el resultado en `featured_sync_log`.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass

import httpx
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.post import Post
from app.models.sync_log import FeaturedSyncLog
from app.services.vault_service import VaultServiceError, vault_service


@dataclass(slots=True)
class FeaturedSyncResult:
    """Resultado de la sincronizacion (lo que termina en el log)."""

    success: bool
    status_code: int | None
    message: str | None
    payload_hash: str


class SistemaBClient:
    """Cliente especializado para el endpoint de contenido destacado."""

    def __init__(self) -> None:
        self.base_url = settings.SISTEMA_B_URL
        self.api_key = settings.SISTEMA_B_API_KEY
        self.timeout = settings.SISTEMA_B_TIMEOUT

    @property
    def featured_endpoint(self) -> str:
        return f"{self.base_url}/api/internal/featured-content"

    def _build_payload(self, post: Post, content_html: str) -> dict[str, str]:
        """Plaintext cifrado que viaja al Sistema B.

        Debe coincidir con el `FeaturedPlaintext` del Sistema B:
        `title`, `excerpt`, `content_html` y `slug`, todos no vacios.
        """
        excerpt = (post.excerpt or "").strip() or self._fallback_excerpt(content_html)
        return {
            "title": post.title,
            "excerpt": excerpt,
            "content_html": content_html,
            "slug": post.slug,
        }

    @staticmethod
    def _fallback_excerpt(content_html: str, limit: int = 200) -> str:
        """Deriva un excerpt no vacio a partir del HTML cuando el post no trae uno."""
        text = re.sub(r"<[^>]+>", " ", content_html)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:limit].rstrip() or "Contenido destacado"

    @staticmethod
    def _hash_payload(payload_json: str) -> str:
        return hashlib.sha256(payload_json.encode("utf-8")).hexdigest()

    async def send_featured_post(
        self,
        post: Post,
        db: AsyncSession,
        *,
        content_html: str,
    ) -> FeaturedSyncResult:
        """Envia un post destacado al Sistema B y registra el resultado.

        Nunca lanza excepciones al caller: todo error se captura y se
        refleja en `FeaturedSyncResult.success = False`.
        """
        payload = self._build_payload(post, content_html)
        payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        payload_hash = self._hash_payload(payload_json)

        try:
            ciphertext = vault_service.encrypt(payload_json)
        except VaultServiceError as e:
            logger.error("Cifrado Vault fallo para post {}: {}", post.id, e)
            return await self._log_and_return(
                db,
                post_id=post.id,
                payload_hash=payload_hash,
                status_code=None,
                message=f"Vault: {e}",
                success=False,
            )

        body = {"post_id": str(post.id), "ciphertext": ciphertext}
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(self.featured_endpoint, json=body, headers=headers)
            ok = 200 <= resp.status_code < 300
            msg = resp.text[:500] if not ok else "ok"
            if not ok:
                logger.warning(
                    "Sistema B respondio {} para post {}: {}",
                    resp.status_code,
                    post.id,
                    msg,
                )
            return await self._log_and_return(
                db,
                post_id=post.id,
                payload_hash=payload_hash,
                status_code=resp.status_code,
                message=msg,
                success=ok,
            )
        except httpx.HTTPError as e:
            logger.exception("Fallo de red hablando con Sistema B: {}", e)
            return await self._log_and_return(
                db,
                post_id=post.id,
                payload_hash=payload_hash,
                status_code=None,
                message=f"HTTP error: {e}",
                success=False,
            )

    async def _log_and_return(
        self,
        db: AsyncSession,
        *,
        post_id: uuid.UUID,
        payload_hash: str,
        status_code: int | None,
        message: str | None,
        success: bool,
    ) -> FeaturedSyncResult:
        log = FeaturedSyncLog(
            post_id=post_id,
            request_payload_hash=payload_hash,
            response_status=status_code,
            response_message=message,
            success=success,
        )
        db.add(log)
        await db.commit()
        return FeaturedSyncResult(
            success=success,
            status_code=status_code,
            message=message,
            payload_hash=payload_hash,
        )


sistema_b_client = SistemaBClient()
