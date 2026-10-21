import os
import time
from threading import Lock
from typing import Callable, Optional

import httpx  # noqa: F401  los tests parchean open_exchange_rate_provider.httpx.get

from app.domain.ports.exchange_rate_provider import ExchangeRateProvider
from app.infrastructure.external.resilient_http import (
    ExternalSourceError,
    RetryPolicy,
    get_json,
)

SOURCE_NAME = "ExchangeRate"

# open.er-api.com publica una tasa nueva una vez al día y, ante abuso, responde
# 429 y bloquea durante 20 minutos. Un único intento (hay tasa de respaldo) y,
# tras un fallo, no se vuelve a consultar de inmediato en cada búsqueda.
DEFAULT_POLICY = dict(timeout_seconds=3.0, max_attempts=1)
FAILURE_BACKOFF_SECONDS = 5 * 60
RATE_LIMITED_BACKOFF_SECONDS = 20 * 60


class OpenExchangeRateProvider(ExchangeRateProvider):
    """Adaptador de la tasa de cambio pública de open.er-api.com."""

    _url = "https://open.er-api.com/v6/latest/USD"

    def __init__(
        self,
        policy: Optional[RetryPolicy] = None,
        clock: Callable[[], float] = time.monotonic,
    ):
        # Variables DRIFT_EXCHANGE_*; ver arc42 §8.13.
        self._policy = policy or RetryPolicy.from_env(
            "DRIFT_EXCHANGE",
            **DEFAULT_POLICY,
        )
        self._clock = clock
        self._rate = None
        self._loaded_at = None
        self._retry_not_before = None
        self._cache_duration_seconds = 12 * 60 * 60
        self._fallback_rate = float(
            os.getenv("USD_TO_COP_RATE", "3250")
        )
        self._lock = Lock()

    def usd_to_cop(self) -> float:
        with self._lock:
            now = self._clock()

            if self._rate and now - self._loaded_at < self._cache_duration_seconds:
                return self._rate

            # Tras un fallo se sirve la última tasa conocida (o la configurada)
            # sin volver a llamar a la fuente hasta que pase la espera.
            if self._retry_not_before is not None and now < self._retry_not_before:
                return self._rate or self._fallback_rate

            try:
                data = get_json(
                    self._url,
                    None,
                    source=SOURCE_NAME,
                    policy=self._policy,
                )

                rate = float(data["rates"]["COP"])
            except ExternalSourceError as error:
                self._back_off(
                    RATE_LIMITED_BACKOFF_SECONDS
                    if error.reason == "rate_limited"
                    else FAILURE_BACKOFF_SECONDS
                )

                return self._rate or self._fallback_rate
            except (httpx.HTTPError, AttributeError, KeyError, TypeError, ValueError):
                # Respuesta con otra forma: se trata como un fallo de la fuente.
                self._back_off(FAILURE_BACKOFF_SECONDS)

                return self._rate or self._fallback_rate

            self._rate = rate
            self._loaded_at = self._clock()
            self._retry_not_before = None

            return rate

    def _back_off(self, seconds: float) -> None:
        self._retry_not_before = self._clock() + seconds
