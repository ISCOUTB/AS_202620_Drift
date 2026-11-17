import logging
import os
from datetime import datetime, timezone
from typing import Callable, List, Optional

import httpx

from app.domain.model.game import Game
from app.domain.model.source_snapshot import SourceSnapshot
from app.domain.ports.game_repository import GameRepository
from app.domain.ports.source_snapshot_store import SourceSnapshotStore
from app.infrastructure.external.resilient_http import ExternalSourceError
from app.infrastructure.game_copy import copy_games
from app.infrastructure.observability import log_event

logger = logging.getLogger("drift")

# 15 minutos: una copia más nueva se usa sin llamar a la fuente.
DEFAULT_FRESH_SECONDS = 15 * 60.0
# 72 horas: una copia más vieja ya no se muestra.
DEFAULT_STALE_SECONDS = 72 * 60 * 60.0

MAX_KEY_LENGTH = 200


def fresh_seconds_from_env() -> float:
    return float(os.getenv("DRIFT_CACHE_FRESH_SECONDS", DEFAULT_FRESH_SECONDS))


def stale_seconds_from_env() -> float:
    return float(os.getenv("DRIFT_CACHE_STALE_SECONDS", DEFAULT_STALE_SECONDS))


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StaleFallbackGameRepository(GameRepository):
    """
    Envuelve una fuente y guarda una copia de cada respuesta (ADR-0015).

    Según la edad de la copia de una búsqueda:

    - menos de `fresh_seconds`: se devuelve la copia sin llamar a la fuente
      (ahorra cuota de la fuente);
    - hasta `stale_seconds`: se llama a la fuente; si falla, se devuelve la
      copia y cada juego lo avisa en `cached_sources`;
    - más vieja, o sin copia: el fallo de la fuente se propaga, igual que
      si este envoltorio no existiera.

    No cambia nada de la fuente envuelta y sirve para cualquiera de ellas.
    """

    def __init__(
        self,
        repository: GameRepository,
        source_name: str,
        store: SourceSnapshotStore,
        fresh_seconds: Optional[float] = None,
        stale_seconds: Optional[float] = None,
        now: Callable[[], datetime] = _utc_now,
    ):
        self._repository = repository
        self._source_name = source_name
        self._store = store
        self._fresh_seconds = (
            fresh_seconds_from_env() if fresh_seconds is None else fresh_seconds
        )
        self._stale_seconds = (
            stale_seconds_from_env() if stale_seconds is None else stale_seconds
        )
        self._now = now

    def search(self, query: str) -> List[Game]:
        key = self._key(query)

        if key is None:
            return self._repository.search(query)

        snapshot = self._store.get(self._source_name, key)

        if snapshot is not None and self._age(snapshot) < self._fresh_seconds:
            return copy_games(snapshot.games)

        try:
            games = self._repository.search(query)
        except (httpx.HTTPError, ExternalSourceError) as error:
            if not self._is_usable(snapshot):
                raise

            return self._from_backup(snapshot, cause=_cause(error))

        self._store.put(self._source_name, key, games, self._now())

        return games

    def last_known(self, query: str) -> Optional[List[Game]]:
        """
        La copia de respaldo de una búsqueda, sin llamar a la fuente.

        La usa quien dejó de esperar a esta fuente por tiempo: en ese caso
        `search` todavía no ha terminado y no puede entregar la copia.
        """

        key = self._key(query)

        if key is None:
            return None

        snapshot = self._store.get(self._source_name, key)

        if not self._is_usable(snapshot):
            return None

        return self._from_backup(snapshot, cause="timeout")

    def _from_backup(self, snapshot: SourceSnapshot, cause: str) -> List[Game]:
        captured_at = snapshot.captured_at.astimezone(timezone.utc).isoformat()
        games = copy_games(snapshot.games)

        for game in games:
            game.cached_sources[self._source_name] = captured_at

        log_event(
            logger,
            "source_served_from_backup",
            source=self._source_name,
            cause=cause,
            age_seconds=round(self._age(snapshot)),
        )

        return games

    def _is_usable(self, snapshot: Optional[SourceSnapshot]) -> bool:
        # Una copia sin juegos no aporta precios: es más honesto avisar que
        # la fuente no respondió que presentar «nada» como dato guardado.
        return (
            snapshot is not None
            and bool(snapshot.games)
            and self._age(snapshot) < self._stale_seconds
        )

    def _age(self, snapshot: SourceSnapshot) -> float:
        return (self._now() - snapshot.captured_at).total_seconds()

    @staticmethod
    def _key(query: str) -> Optional[str]:
        key = " ".join(query.lower().split())

        if not key or len(key) > MAX_KEY_LENGTH:
            return None

        return key


def _cause(error: Exception) -> str:
    if isinstance(error, ExternalSourceError):
        return error.reason

    return "timeout" if isinstance(error, httpx.TimeoutException) else "error"
