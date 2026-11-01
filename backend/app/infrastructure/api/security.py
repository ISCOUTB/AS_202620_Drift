"""
Controles de seguridad de la API (modelo de amenazas S13: A2, A3, A5 y A10).

- `require_admin_token`: protege las operaciones administrativas
  (sincronización del catálogo y métricas) con un token de servicio.
- `SlidingWindowRateLimiter`: limita las peticiones por cliente en las rutas
  que generan llamadas a fuentes externas.

Decisión en ADR-0011 y ADR-0012.
"""

import hmac
import os
from collections import deque
from threading import Lock
from time import monotonic
from typing import Optional

from fastapi import Header, HTTPException, Request

ADMIN_TOKEN_ENV = "DRIFT_ADMIN_TOKEN"
RATE_LIMIT_ENV = "DRIFT_RATE_LIMIT_PER_MINUTE"
TRUST_FORWARDED_FOR_ENV = "DRIFT_TRUST_FORWARDED_FOR"

DEFAULT_RATE_LIMIT_PER_MINUTE = 60


def require_admin_token(
    authorization: Optional[str] = Header(default=None),
) -> None:
    """Exige `Authorization: Bearer <DRIFT_ADMIN_TOKEN>`.

    Sin cabecera, o con un token incorrecto: 401. Falla cerrado: si el token
    no está configurado en el servidor, la operación queda deshabilitada (403)
    en lugar de quedar abierta.
    """

    scheme, _, received = (authorization or "").partition(" ")

    if scheme.lower() != "bearer" or not received:
        raise HTTPException(
            status_code=401,
            detail={"reason": "invalid_admin_token"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    expected = os.getenv(ADMIN_TOKEN_ENV, "")

    if not expected:
        raise HTTPException(
            status_code=403,
            detail={"reason": "admin_operation_disabled"},
        )

    if not hmac.compare_digest(
        received.encode(),
        expected.encode(),
    ):
        raise HTTPException(
            status_code=401,
            detail={"reason": "invalid_admin_token"},
            headers={"WWW-Authenticate": "Bearer"},
        )


def client_ip(request: Request) -> str:
    """IP del cliente usada para limitar la tasa.

    Detrás de un proxy (Azure App Service, Traefik en Dokploy) todas las
    peticiones llegan desde la IP del proxy. Con `DRIFT_TRUST_FORWARDED_FOR=true`
    se usa la última entrada de `X-Forwarded-For`, que es la que agrega el
    proxy de confianza; las anteriores las puede escribir el cliente.
    """

    if os.getenv(TRUST_FORWARDED_FOR_ENV, "").lower() in {"1", "true", "yes"}:
        forwarded = request.headers.get("x-forwarded-for", "")
        hops = [hop.strip() for hop in forwarded.split(",") if hop.strip()]

        if hops:
            return _without_port(hops[-1])

    return request.client.host if request.client else "desconocido"


def _without_port(address: str) -> str:
    """Azure App Service escribe `IP:puerto`; el puerto cambia en cada conexión."""

    if address.startswith("["):  # IPv6 con puerto: [2001:db8::1]:51234
        return address[1:].split("]", 1)[0]

    if address.count(":") == 1:  # IPv4 con puerto: 1.2.3.4:51234
        return address.split(":", 1)[0]

    return address


def rate_limit_from_env() -> int:
    raw = os.getenv(RATE_LIMIT_ENV, "")

    try:
        return max(0, int(raw)) if raw else DEFAULT_RATE_LIMIT_PER_MINUTE
    except ValueError:
        return DEFAULT_RATE_LIMIT_PER_MINUTE


class SlidingWindowRateLimiter:
    """Ventana deslizante en memoria del proceso, por clave de cliente.

    `limit` peticiones cada `window_seconds`. Con `limit=0` no limita.
    Igual que las cachés de DRIFT, vive en un proceso (ADR-0008): con varias
    instancias, cada una lleva su propia cuenta.
    """

    def __init__(self, limit, window_seconds=60.0, clock=monotonic, max_clients=10_000):
        self.limit = limit
        self.window_seconds = window_seconds
        self._clock = clock
        self._max_clients = max_clients
        self._hits = {}
        self._lock = Lock()

    def check(self, key):
        """Devuelve `(permitido, segundos_para_reintentar)`."""

        if self.limit <= 0:
            return True, 0

        now = self._clock()
        cutoff = now - self.window_seconds

        with self._lock:
            hits = self._hits.get(key)

            if hits is None:
                if len(self._hits) >= self._max_clients:
                    self._forget_idle_clients(cutoff)
                hits = self._hits[key] = deque()

            while hits and hits[0] <= cutoff:
                hits.popleft()

            if len(hits) >= self.limit:
                retry_after = max(1, int(hits[0] + self.window_seconds - now) + 1)
                return False, retry_after

            hits.append(now)
            return True, 0

    def _forget_idle_clients(self, cutoff):
        # Evita que la tabla crezca sin límite con muchas IP distintas.
        for key in [k for k, hits in self._hits.items() if not hits or hits[-1] <= cutoff]:
            del self._hits[key]
