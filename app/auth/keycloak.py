"""Cliente Keycloak.

Encapsula:
- Construccion de la URL de login (Authorization Code + state).
- Intercambio code -> tokens.
- Validacion del JWT contra el JWKS publico del realm.
- Extraccion de roles (realm + client) y datos de usuario.
- URL de logout para terminar SSO.

El 2FA / MFA se aplica del lado de Keycloak (politicas del realm),
asi que esta capa solo necesita confiar en el JWT que recibe.
"""

from __future__ import annotations

import secrets
from typing import Any
from urllib.parse import urlencode

import httpx
from jose import jwt
from jose.exceptions import JWTError
from loguru import logger

from app.config import settings


class KeycloakAuthError(Exception):
    """Error generico durante el flujo Keycloak."""


class KeycloakClient:
    """Cliente minimalista para el flujo OIDC Authorization Code."""

    def __init__(self) -> None:
        self.base_url = settings.KEYCLOAK_URL
        self.realm = settings.KEYCLOAK_REALM
        self.client_id = settings.KEYCLOAK_CLIENT_ID
        self.client_secret = settings.KEYCLOAK_CLIENT_SECRET
        self.redirect_uri = settings.KEYCLOAK_REDIRECT_URI
        self._jwks_cache: dict[str, Any] | None = None

    # ---------- Endpoints OIDC ----------
    @property
    def realm_url(self) -> str:
        return f"{self.base_url}/realms/{self.realm}"

    @property
    def authorize_endpoint(self) -> str:
        return f"{self.realm_url}/protocol/openid-connect/auth"

    @property
    def token_endpoint(self) -> str:
        return f"{self.realm_url}/protocol/openid-connect/token"

    @property
    def logout_endpoint(self) -> str:
        return f"{self.realm_url}/protocol/openid-connect/logout"

    @property
    def jwks_endpoint(self) -> str:
        return f"{self.realm_url}/protocol/openid-connect/certs"

    @property
    def issuer(self) -> str:
        return self.realm_url

    # ---------- Flujo OIDC ----------
    def build_login_url(self, state: str | None = None) -> tuple[str, str]:
        """Construye la URL de Keycloak para iniciar Authorization Code.

        Devuelve (url, state). El `state` debe guardarse en sesion y
        validarse al regreso para mitigar CSRF.
        """
        state = state or secrets.token_urlsafe(32)
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid profile email",
            "state": state,
        }
        return f"{self.authorize_endpoint}?{urlencode(params)}", state

    def build_logout_url(self, post_logout_redirect: str | None = None) -> str:
        """URL para cerrar sesion en Keycloak."""
        redirect = post_logout_redirect or settings.KEYCLOAK_POST_LOGOUT_URI or settings.APP_URL
        params = {
            "client_id": self.client_id,
            "post_logout_redirect_uri": redirect,
        }
        return f"{self.logout_endpoint}?{urlencode(params)}"

    async def exchange_code_for_tokens(self, code: str) -> dict[str, Any]:
        """Intercambia un authorization code por tokens (access/refresh/id)."""
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    self.token_endpoint,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
            if resp.status_code != 200:
                logger.error(
                    "Keycloak token exchange fallo: status={} body={}",
                    resp.status_code,
                    resp.text,
                )
                raise KeycloakAuthError("No se pudo intercambiar el code por tokens")
            return resp.json()
        except httpx.HTTPError as e:
            logger.exception("Error HTTP hablando con Keycloak: {}", e)
            raise KeycloakAuthError("Fallo de comunicacion con Keycloak") from e

    async def _get_jwks(self) -> dict[str, Any]:
        """Descarga (y cachea en memoria) el JWKS del realm."""
        if self._jwks_cache is not None:
            return self._jwks_cache
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(self.jwks_endpoint)
            resp.raise_for_status()
        self._jwks_cache = resp.json()
        return self._jwks_cache

    async def decode_and_validate(self, token: str) -> dict[str, Any]:
        """Decodifica y valida la firma + claims del JWT."""
        try:
            jwks = await self._get_jwks()
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            key = next((k for k in jwks["keys"] if k.get("kid") == kid), None)
            if not key:
                raise KeycloakAuthError("Token firmado con una clave desconocida")

            return jwt.decode(
                token,
                key,
                algorithms=[key.get("alg", "RS256")],
                audience=None,  # Keycloak no siempre setea aud al client_id
                issuer=self.issuer,
                options={"verify_aud": False},
            )
        except JWTError as e:
            logger.warning("JWT invalido: {}", e)
            raise KeycloakAuthError(f"Token invalido: {e}") from e

    # ---------- Utilidades ----------
    def extract_roles(self, claims: dict[str, Any]) -> list[str]:
        """Combina realm_access.roles + resource_access[client_id].roles."""
        roles: list[str] = []
        roles.extend(claims.get("realm_access", {}).get("roles", []))
        client_roles = (
            claims.get("resource_access", {}).get(self.client_id, {}).get("roles", [])
        )
        roles.extend(client_roles)
        return list(dict.fromkeys(roles))  # dedup conservando orden

    def pick_app_role(self, roles: list[str]) -> str:
        """Selecciona el rol de mayor privilegio reconocido por la app."""
        priority = ["admin", "editor", "user"]
        for role in priority:
            if role in roles:
                return role
        return "user"


keycloak_client = KeycloakClient()
