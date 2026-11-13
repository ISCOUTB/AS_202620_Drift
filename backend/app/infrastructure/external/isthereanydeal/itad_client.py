import logging
import os
import time
from collections import deque
from threading import Lock
from typing import Any, Callable, Optional

import httpx  # noqa: F401  los tests parchean itad_client.httpx.get y .post

from app.infrastructure.external.resilient_http import (
    ExternalSourceError,
    RetryPolicy,
    TimeBudget,
    get_json,
)
from app.infrastructure.observability import log_event

logger = logging.getLogger("drift")

SOURCE_NAME = "IsThereAnyDeal"

BASE_URL = "https://api.isthereanydeal.com"

# IsThereAnyDeal permite 1.000 llamadas cada 5 minutos por aplicación. DRIFT
# se detiene antes, en 900, para no llegar nunca al bloqueo.
DEFAULT_QUOTA_LIMIT = 900
QUOTA_WINDOW_SECONDS = 300.0

# Si aun así la fuente responde 429, no se la vuelve a llamar por un rato.
DEFAULT_PAUSE_SECONDS = 60.0

DEFAULT_POLICY = dict(timeout_seconds=3.0, max_attempts=2)
DEFAULT_TOTAL_DEADLINE_SECONDS = 3.0


class ItadClient:
    """
    Llamadas a la API de IsThereAnyDeal con control de cuota (ADR-0015).

    Lo comparten el adaptador de precios y el del historial, para que las
    llamadas de los dos cuenten contra el mismo límite.

    Cuando la cuota propia se agota, o la fuente respondió 429 hace poco, la
    llamada falla de inmediato con `rate_limited` sin salir a la red. Quien
    llama lo trata como cualquier fallo de la fuente: la búsqueda responde
    con su copia de respaldo.

    La llave viaja en una cabecera y nunca se registra.
    """

    def __init__(
        self,
        api_key: str,
        policy: Optional[RetryPolicy] = None,
        quota_limit: Optional[int] = None,
        pause_seconds: float = DEFAULT_PAUSE_SECONDS,
        sleep: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
    ):
        # Variables DRIFT_ITAD_*.
        self._policy = policy or RetryPolicy.from_env(
            "DRIFT_ITAD",
            default_total_deadline_seconds=DEFAULT_TOTAL_DEADLINE_SECONDS,
            **DEFAULT_POLICY,
        )
        self._headers = {
            "ITAD-API-Key": api_key,
            "Accept": "application/json",
            "User-Agent": "DRIFT/1.0 (proyecto academico AS_202620 UTB)",
        }
        self._quota_limit = (
            int(os.getenv("DRIFT_ITAD_QUOTA_LIMIT", DEFAULT_QUOTA_LIMIT))
            if quota_limit is None
            else quota_limit
        )
        self._pause_seconds = pause_seconds
        self._sleep = sleep
        self._monotonic = monotonic
        self._calls: deque = deque()
        self._paused_until: Optional[float] = None
        self._lock = Lock()

    def new_budget(self, seconds: Optional[float] = None) -> TimeBudget:
        """
        Plazo total compartido por las llamadas de una misma operación.

        Sin `seconds` es el plazo de la búsqueda (3 s), igual al de las
        demás fuentes secundarias. El historial pide uno más largo porque
        encadena tres llamadas y nadie más espera por él.
        """

        if seconds is None:
            return TimeBudget.from_policy(self._policy)

        return TimeBudget(seconds)

    def get(self, path: str, params: dict, budget: Optional[TimeBudget] = None):
        return self._request(path, params, None, budget)

    def post(
        self,
        path: str,
        body: Any,
        params: Optional[dict] = None,
        budget: Optional[TimeBudget] = None,
    ):
        return self._request(path, params, body, budget)

    def quota_snapshot(self) -> dict:
        """Uso de la cuota en la ventana actual, para `/metrics`."""

        with self._lock:
            now = self._monotonic()
            self._forget_old_calls(now)

            return {
                "metric": "drift_itad_quota",
                "calls_in_window": len(self._calls),
                "limit": self._quota_limit,
                "window_seconds": int(QUOTA_WINDOW_SECONDS),
                "paused": self._paused_until is not None
                and now < self._paused_until,
            }

    def _request(self, path, params, body, budget):
        self._reserve_call()

        try:
            return get_json(
                f"{BASE_URL}{path}",
                params,
                source=SOURCE_NAME,
                policy=self._policy,
                sleep=self._sleep,
                headers=self._headers,
                budget=budget,
                json_body=body,
            )
        except ExternalSourceError as error:
            if error.reason == "rate_limited":
                self._pause()

            raise

    def _reserve_call(self) -> None:
        with self._lock:
            now = self._monotonic()

            if self._paused_until is not None and now < self._paused_until:
                raise ExternalSourceError(SOURCE_NAME, "rate_limited")

            self._forget_old_calls(now)

            if len(self._calls) >= self._quota_limit:
                exhausted = True
            else:
                exhausted = False
                self._calls.append(now)

        if exhausted:
            log_event(
                logger,
                "source_quota_exhausted",
                source=SOURCE_NAME,
                limit=self._quota_limit,
                window_seconds=int(QUOTA_WINDOW_SECONDS),
            )

            raise ExternalSourceError(SOURCE_NAME, "rate_limited")

    def _forget_old_calls(self, now: float) -> None:
        while self._calls and now - self._calls[0] >= QUOTA_WINDOW_SECONDS:
            self._calls.popleft()

    def _pause(self) -> None:
        with self._lock:
            self._paused_until = self._monotonic() + self._pause_seconds

        log_event(
            logger,
            "source_paused",
            source=SOURCE_NAME,
            paused_seconds=self._pause_seconds,
        )
