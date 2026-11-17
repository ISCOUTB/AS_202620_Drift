import base64
import json
import time
from typing import Callable, Optional
from urllib.parse import urlencode

import httpx

from app.domain.model.account import GoogleIdentity
from app.domain.ports.identity_provider import (
    IdentityProvider,
    IdentityProviderUnavailable,
    IdentityRejected,
)

AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"

ISSUERS = {"https://accounts.google.com", "accounts.google.com"}

TIMEOUT_SECONDS = 5.0


class GoogleIdentityProvider(IdentityProvider):
    """
    Inicio de sesión con Google (OpenID Connect, flujo de código).

    El servidor cambia el código por un `id_token` hablando directamente con
    Google por HTTPS. Por eso no se verifica la firma del token: OpenID
    Connect lo permite cuando el token llega por ese canal y no a través del
    navegador. Sí se comprueban el emisor, el destinatario, el vencimiento,
    el `nonce` y que el correo esté verificado.

    Ni el código, ni los tokens, ni el secreto del cliente se registran.
    Solo se pide lo mínimo: identificador, correo, nombre y foto.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        clock: Callable[[], float] = time.time,
    ):
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri
        self._clock = clock

    def authorization_url(self, state: str, nonce: str) -> str:
        return (
            AUTHORIZATION_URL
            + "?"
            + urlencode(
                {
                    "client_id": self._client_id,
                    "redirect_uri": self._redirect_uri,
                    "response_type": "code",
                    "scope": "openid email profile",
                    "state": state,
                    "nonce": nonce,
                    "prompt": "select_account",
                }
            )
        )

    def identify(self, code: str, nonce: str) -> GoogleIdentity:
        try:
            response = httpx.post(
                TOKEN_URL,
                data={
                    "code": code,
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "redirect_uri": self._redirect_uri,
                    "grant_type": "authorization_code",
                },
                timeout=TIMEOUT_SECONDS,
            )
        except httpx.HTTPError as error:
            raise IdentityProviderUnavailable() from error

        if response.status_code >= 500:
            raise IdentityProviderUnavailable()

        if response.status_code != 200:
            # Código vencido, ya usado o que no corresponde a este cliente.
            raise IdentityRejected("code_rejected")

        try:
            id_token = response.json().get("id_token")
        except (ValueError, AttributeError) as error:
            raise IdentityRejected("invalid_response") from error

        claims = _claims(id_token)

        return self._identity(claims, nonce)

    def _identity(self, claims: dict, nonce: str) -> GoogleIdentity:
        expires_at = claims.get("exp")

        if claims.get("iss") not in ISSUERS:
            raise IdentityRejected("wrong_issuer")

        if claims.get("aud") != self._client_id:
            raise IdentityRejected("wrong_audience")

        if (
            isinstance(expires_at, bool)
            or not isinstance(expires_at, (int, float))
            or expires_at <= self._clock()
        ):
            raise IdentityRejected("expired")

        if not nonce or claims.get("nonce") != nonce:
            raise IdentityRejected("wrong_nonce")

        subject = claims.get("sub")
        email = claims.get("email")

        if not isinstance(subject, str) or not subject:
            raise IdentityRejected("missing_subject")

        if not isinstance(email, str) or claims.get("email_verified") is not True:
            raise IdentityRejected("email_not_verified")

        return GoogleIdentity(
            subject=subject,
            email=email,
            name=_text(claims.get("name")) or email.split("@")[0],
            picture=_text(claims.get("picture")),
        )


def _claims(id_token) -> dict:
    """Los datos del `id_token` (su parte central, en base64)."""

    if not isinstance(id_token, str) or id_token.count(".") != 2:
        raise IdentityRejected("invalid_token")

    payload = id_token.split(".")[1]

    try:
        decoded = base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))
        claims = json.loads(decoded)
    except ValueError as error:  # incluye UnicodeDecodeError
        raise IdentityRejected("invalid_token") from error

    if not isinstance(claims, dict):
        raise IdentityRejected("invalid_token")

    return claims


def _text(value) -> Optional[str]:
    return value[:300] if isinstance(value, str) and value else None
