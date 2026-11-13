from collections import OrderedDict
from datetime import datetime
from threading import Lock
from typing import List, Optional

from app.domain.model.game import Game
from app.domain.model.source_snapshot import SourceSnapshot
from app.domain.ports.source_snapshot_store import SourceSnapshotStore
from app.infrastructure.game_copy import copy_games

DEFAULT_MAX_ENTRIES = 500


class InMemorySourceSnapshotStore(SourceSnapshotStore):
    """
    Copias de respaldo en la memoria del proceso.

    Se usa sola donde no hay PostgreSQL (Azure, Vercel, el equipo de quien
    desarrolla) y como segundo respaldo cuando PostgreSQL no responde. Se
    pierde al reiniciar. El número de entradas está acotado para no crecer
    sin límite: al llenarse se descarta la que lleva más tiempo sin usarse.
    """

    def __init__(self, max_entries: int = DEFAULT_MAX_ENTRIES):
        self._max_entries = max_entries
        self._entries: "OrderedDict[tuple, SourceSnapshot]" = OrderedDict()
        self._lock = Lock()

    def get(self, source: str, key: str) -> Optional[SourceSnapshot]:
        with self._lock:
            snapshot = self._entries.get((source, key))

            if snapshot is None:
                return None

            self._entries.move_to_end((source, key))

        return SourceSnapshot(
            games=copy_games(snapshot.games),
            captured_at=snapshot.captured_at,
        )

    def put(
        self,
        source: str,
        key: str,
        games: List[Game],
        captured_at: datetime,
    ) -> None:
        snapshot = SourceSnapshot(
            games=copy_games(games),
            captured_at=captured_at,
        )

        with self._lock:
            self._entries[(source, key)] = snapshot
            self._entries.move_to_end((source, key))

            while len(self._entries) > self._max_entries:
                self._entries.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()
