import os
import time
from threading import Lock

import httpx

from app.domain.ports.exchange_rate_provider import ExchangeRateProvider


class OpenExchangeRateProvider(ExchangeRateProvider):
    """Adaptador de la tasa de cambio pública de open.er-api.com."""

    _url = "https://open.er-api.com/v6/latest/USD"

    def __init__(self):
        self._rate = None
        self._loaded_at = None
        self._cache_duration_seconds = 12 * 60 * 60
        self._fallback_rate = float(
            os.getenv("USD_TO_COP_RATE", "3250")
        )
        self._lock = Lock()

    def usd_to_cop(self) -> float:
        with self._lock:
            if self._rate and time.monotonic() - self._loaded_at < self._cache_duration_seconds:
                return self._rate

            try:
                response = httpx.get(
                    self._url,
                    timeout=5.0,
                )

                response.raise_for_status()

                rate = float(response.json()["rates"]["COP"])
            except (httpx.HTTPError, AttributeError, KeyError, TypeError, ValueError):
                # Sin tasa actualizada se usa la última conocida o la configurada.
                return self._rate or self._fallback_rate

            self._rate = rate
            self._loaded_at = time.monotonic()

            return rate
