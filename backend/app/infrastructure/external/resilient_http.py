import logging
import os
import random
import time
from dataclasses import dataclass
from typing import Any, Callable, Optional

import httpx

from app.infrastructure.observability import log_event

logger = logging.getLogger("drift")


class ExternalSourceError(Exception):
    """
    Una fuente externa no pudo entregar una respuesta utilizable.

    Vive en infraestructura: el dominio y los casos de uso no conocen ni
    `httpx` ni esta clase. `reason` toma uno de estos valores:
    `timeout`, `connection`, `rate_limited`, `server_error`,
    `client_error` o `invalid_response`.
    """

    def __init__(
        self,
        source: str,
        reason: str,
        status_code: Optional[int] = None,
    ):
        super().__init__(f"{source}: {reason}")
        self.source = source
        self.reason = reason
        self.status_code = status_code


@dataclass(frozen=True)
class RetryPolicy:
    """
    `max_attempts` cuenta intentos totales: 2 significa una llamada inicial
    y un único reintento.

    `timeout_seconds` se pasa a `httpx`, que lo aplica por separado a la
    conexión, la lectura, la escritura y la espera de un cliente del pool;
    no es un plazo total de la llamada.
    """

    timeout_seconds: float = 3.0
    max_attempts: int = 2
    backoff_base_seconds: float = 0.25
    backoff_max_seconds: float = 2.0
    max_retry_after_seconds: float = 2.0

    def __post_init__(self):
        if self.max_attempts < 1:
            raise ValueError("max_attempts debe ser al menos 1")

        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds debe ser positivo")

    @classmethod
    def from_env(cls, prefix: str) -> "RetryPolicy":
        """Lee `<prefix>_TIMEOUT_SECONDS`, `_MAX_ATTEMPTS`, etc."""

        defaults = cls()

        return cls(
            timeout_seconds=float(
                os.getenv(f"{prefix}_TIMEOUT_SECONDS", defaults.timeout_seconds)
            ),
            max_attempts=int(
                os.getenv(f"{prefix}_MAX_ATTEMPTS", defaults.max_attempts)
            ),
            backoff_base_seconds=float(
                os.getenv(
                    f"{prefix}_BACKOFF_BASE_SECONDS",
                    defaults.backoff_base_seconds,
                )
            ),
            backoff_max_seconds=float(
                os.getenv(
                    f"{prefix}_BACKOFF_MAX_SECONDS",
                    defaults.backoff_max_seconds,
                )
            ),
            max_retry_after_seconds=float(
                os.getenv(
                    f"{prefix}_MAX_RETRY_AFTER_SECONDS",
                    defaults.max_retry_after_seconds,
                )
            ),
        )

    def backoff_seconds(
        self,
        failed_attempt: int,
        uniform: Callable[[], float] = random.random,
    ) -> float:
        """Backoff exponencial con jitter completo, acotado por el máximo."""

        ceiling = min(
            self.backoff_max_seconds,
            self.backoff_base_seconds * (2 ** (failed_attempt - 1)),
        )

        return uniform() * ceiling


def _retry_after_seconds(response: httpx.Response) -> Optional[float]:
    """Solo se interpreta la forma en segundos; la fecha HTTP se ignora."""

    value = response.headers.get("Retry-After")

    if value is None:
        return None

    try:
        seconds = float(value)
    except (TypeError, ValueError):
        return None

    return seconds if seconds >= 0 else None


def get_json(
    url: str,
    params: dict,
    *,
    source: str,
    policy: RetryPolicy,
    sleep: Callable[[float], None] = time.sleep,
    uniform: Callable[[], float] = random.random,
) -> Any:
    """
    GET con timeout explícito y reintentos solo ante fallos transitorios.

    Transitorios: timeout, errores de conexión, HTTP 429 y HTTP 5xx.
    Permanentes (sin reintento): el resto de 4xx y un cuerpo que no es JSON.
    El GET es una lectura sin efectos, por lo que repetirlo es seguro.

    Cada fallo final se eleva como `ExternalSourceError`. Los registros no
    incluyen la URL ni los parámetros: la búsqueda del usuario no se registra.
    """

    started_at = time.monotonic()

    for attempt in range(1, policy.max_attempts + 1):
        retry_after = None

        try:
            response = httpx.get(
                url,
                params=params,
                timeout=policy.timeout_seconds,
            )
            response.raise_for_status()
            return _decode_json(response, source)

        except ExternalSourceError as error:
            _log_failure(source, error, attempt, policy, started_at)
            raise

        except httpx.HTTPStatusError as error:
            status_code = error.response.status_code

            if status_code == 429:
                reason = "rate_limited"
                retry_after = _retry_after_seconds(error.response)
            elif status_code >= 500:
                reason = "server_error"
            else:
                reason = "client_error"

            failure = ExternalSourceError(source, reason, status_code)
            failure.__cause__ = error
            transient = reason != "client_error"

        except httpx.TimeoutException as error:
            failure = ExternalSourceError(source, "timeout")
            failure.__cause__ = error
            transient = True

        except httpx.TransportError as error:
            failure = ExternalSourceError(source, "connection")
            failure.__cause__ = error
            transient = True

        delay = None

        if transient and attempt < policy.max_attempts:
            delay = _wait_before_retry(
                failure,
                attempt,
                retry_after,
                policy,
                uniform,
            )

        if delay is None:
            _log_failure(source, failure, attempt, policy, started_at)
            raise failure

        log_event(
            logger,
            "external_retry",
            source=source,
            reason=failure.reason,
            http_status=failure.status_code,
            attempt=attempt,
            max_attempts=policy.max_attempts,
            delay_ms=round(delay * 1000, 2),
            elapsed_ms=_elapsed_ms(started_at),
        )

        sleep(delay)

    # Inalcanzable: el último intento siempre devuelve o eleva.
    raise ExternalSourceError(source, "connection")


def _wait_before_retry(
    failure: ExternalSourceError,
    attempt: int,
    retry_after: Optional[float],
    policy: RetryPolicy,
    uniform: Callable[[], float],
) -> Optional[float]:
    """Segundos a esperar antes de reintentar, o None si no conviene."""

    if failure.reason == "rate_limited" and retry_after is not None:
        # Si Steam pide esperar más de lo tolerable, reintentar antes
        # ignoraría su indicación: se falla rápido y se degrada.
        if retry_after > policy.max_retry_after_seconds:
            return None

        return retry_after

    return policy.backoff_seconds(attempt, uniform)


def _decode_json(response: httpx.Response, source: str) -> Any:
    try:
        return response.json()
    except ValueError as error:
        failure = ExternalSourceError(source, "invalid_response")
        failure.__cause__ = error
        raise failure


def _elapsed_ms(started_at: float) -> float:
    return round((time.monotonic() - started_at) * 1000, 2)


def _log_failure(
    source: str,
    failure: ExternalSourceError,
    attempt: int,
    policy: RetryPolicy,
    started_at: float,
) -> None:
    log_event(
        logger,
        "external_request_failed",
        source=source,
        reason=failure.reason,
        http_status=failure.status_code,
        attempts=attempt,
        max_attempts=policy.max_attempts,
        elapsed_ms=_elapsed_ms(started_at),
    )
