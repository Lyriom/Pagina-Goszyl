"""Servicio de cifrado/descifrado contra HashiCorp Vault Transit.

Vault Transit acepta plaintext en base64 y devuelve un ciphertext con
prefijo `vault:vN:`. Este wrapper expone metodos sincronos sencillos
(`encrypt` / `decrypt`) con reintentos basicos y logging estructurado.
"""

from __future__ import annotations

import base64
import time
from typing import Final

import hvac
from hvac.exceptions import VaultError
from loguru import logger

from app.config import settings

_MAX_RETRIES: Final[int] = 3
_RETRY_BACKOFF_SECONDS: Final[float] = 0.5


class VaultServiceError(Exception):
    """Error generico al hablar con Vault."""


class VaultService:
    """Wrapper sobre `hvac.Client` para Transit (cifrado simetrico)."""

    def __init__(self) -> None:
        self._client = hvac.Client(
            url=settings.VAULT_URL,
            token=settings.VAULT_TOKEN,
            timeout=10,
        )
        self._key_name = settings.VAULT_TRANSIT_KEY
        self._mount = settings.VAULT_TRANSIT_MOUNT

    # ---------- Helpers ----------
    def _ensure_authenticated(self) -> None:
        if not self._client.is_authenticated():
            raise VaultServiceError("Vault no autenticado: revisa VAULT_TOKEN")

    @staticmethod
    def _to_b64(plaintext: str) -> str:
        return base64.b64encode(plaintext.encode("utf-8")).decode("ascii")

    @staticmethod
    def _from_b64(payload: str) -> str:
        return base64.b64decode(payload.encode("ascii")).decode("utf-8")

    # ---------- API publica ----------
    def encrypt(self, plaintext: str) -> str:
        """Cifra `plaintext` con la transit key y devuelve el ciphertext.

        Reintenta hasta _MAX_RETRIES veces con backoff lineal.
        """
        self._ensure_authenticated()
        b64 = self._to_b64(plaintext)
        last_err: Exception | None = None

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                resp = self._client.secrets.transit.encrypt_data(
                    name=self._key_name,
                    plaintext=b64,
                    mount_point=self._mount,
                )
                ciphertext = resp["data"]["ciphertext"]
                logger.debug("Vault encrypt ok (key={})", self._key_name)
                return ciphertext
            except (VaultError, KeyError) as e:
                last_err = e
                logger.warning(
                    "Vault encrypt fallo (intento {}/{}): {}", attempt, _MAX_RETRIES, e
                )
                time.sleep(_RETRY_BACKOFF_SECONDS * attempt)

        raise VaultServiceError(f"No se pudo cifrar tras {_MAX_RETRIES} intentos") from last_err

    def decrypt(self, ciphertext: str) -> str:
        """Descifra un ciphertext de Vault Transit. Util para verificacion."""
        self._ensure_authenticated()
        last_err: Exception | None = None

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                resp = self._client.secrets.transit.decrypt_data(
                    name=self._key_name,
                    ciphertext=ciphertext,
                    mount_point=self._mount,
                )
                b64 = resp["data"]["plaintext"]
                return self._from_b64(b64)
            except (VaultError, KeyError) as e:
                last_err = e
                logger.warning(
                    "Vault decrypt fallo (intento {}/{}): {}", attempt, _MAX_RETRIES, e
                )
                time.sleep(_RETRY_BACKOFF_SECONDS * attempt)

        raise VaultServiceError(f"No se pudo descifrar tras {_MAX_RETRIES} intentos") from last_err


vault_service = VaultService()
