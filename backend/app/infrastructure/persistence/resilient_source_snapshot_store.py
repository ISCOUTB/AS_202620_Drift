import logging
import time
from datetime import datetime
from threading import Lock
from typing import Callable, List, Optional

from app.domain.model.game import Game
from app.domain.model.source_snapshot import SourceSnapshot
from app.domain.ports.source_snapshot_store import SourceSnapshotStore
from app.infrastructure.observability import log_event

logger = logging.getLogger("drift")

DEFAULT_COOLDOWN_SECONDS = 30.0


class ResilientSourceSnapshotStore(SourceSnapshotStore):
    """
    Almacén duradero con un segundo respaldo en memoria (ADR-0014).

    - Cada copia se escribe en los dos almacenes.
    - Se lee de los dos y se devuelve la copia más reciente.
    - Si el almacén duradero falla, se deja de llamarlo durante
      `cooldown_seconds` y se sigue solo con la memoria. Así una base de
      datos caída no le suma su tiempo de espera a cada búsqueda.

    Nunca lanza errores: el respaldo no puede tumbar la búsqueda.
    """

    def __init__(
        self,
        primary: SourceSnapshotStore,
        fallback: SourceSnapshotStore,
        cooldown_seconds: float = DEFAULT_COOLDOWN_SECONDS,
        monotonic: Callable[[], float] = time.monotonic,
    ):
        self._primary = primary
        self._fallback = fallback
        self._cooldown_seconds = cooldown_seconds
        self._monotonic = monotonic
        self._paused_until: Optional[float] = None
        self._lock = Lock()

    def get(self, source: str, key: str) -> Optional[SourceSnapshot]:
        remembered = self._fallback.get(source, key)
        durable = None

        if self._primary_is_available():
            try:
                durable = self._primary.get(source, key)
            except Exception as error:  # noqa: BLE001  el respaldo nunca propaga
                self._pause_primary("get", error)
            else:
                self._resume_primary()

        if durable is None:
            return remembered

        if remembered is None or durable.captured_at >= remembered.captured_at:
            return durable

        return remembered

    def put(
        self,
        source: str,
        key: str,
        games: List[Game],
        captured_at: datetime,
    ) -> None:
        self._fallback.put(source, key, games, captured_at)

        if not self._primary_is_available():
            return

        try:
            self._primary.put(source, key, games, captured_at)
        except Exception as error:  # noqa: BLE001  el respaldo nunca propaga
            self._pause_primary("put", error)
        else:
            self._resume_primary()

    def is_degraded(self) -> bool:
        """`True` mientras el almacén duradero está en pausa por un fallo."""

        return not self._primary_is_available()

    def _primary_is_available(self) -> bool:
        with self._lock:
            return (
                self._paused_until is None
                or self._monotonic() >= self._paused_until
            )

    def _pause_primary(self, operation: str, error: Exception) -> None:
        with self._lock:
            self._paused_until = self._monotonic() + self._cooldown_seconds

        # Solo el tipo del error: el mensaje podría traer datos de conexión.
        log_event(
            logger,
            "snapshot_store_unavailable",
            operation=operation,
            error=type(error).__name__,
            paused_seconds=self._cooldown_seconds,
        )

    def _resume_primary(self) -> None:
        with self._lock:
            was_paused = self._paused_until is not None
            self._paused_until = None

        if was_paused:
            log_event(logger, "snapshot_store_recovered")
