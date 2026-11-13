import json
import time
from datetime import datetime
from threading import Lock
from typing import Callable, List, Optional

from psycopg.types.json import Jsonb

from app.domain.model.game import Game
from app.domain.model.source_snapshot import SourceSnapshot
from app.domain.ports.source_snapshot_store import SourceSnapshotStore
from app.infrastructure.persistence.postgres_database import PostgresDatabase

DEFAULT_MAX_ROWS = 5000
DEFAULT_MAX_PAYLOAD_BYTES = 256 * 1024
DEFAULT_CLEANUP_INTERVAL_SECONDS = 600.0


class PostgresSourceSnapshotStore(SourceSnapshotStore):
    """
    Copias de respaldo en PostgreSQL: sobreviven a reinicios y despliegues.

    Este adaptador sí lanza los errores de la base de datos. Quien lo usa
    es `ResilientSourceSnapshotStore`, que los convierte en «sin respaldo»
    y deja de llamar a la base por un rato.

    La tabla está acotada: cada cierto tiempo se borran las copias más
    viejas que `max_age_seconds` y las que sobran de `max_rows`, para que
    búsquedas inventadas no llenen el disco.
    """

    def __init__(
        self,
        database: PostgresDatabase,
        max_age_seconds: float,
        max_rows: int = DEFAULT_MAX_ROWS,
        max_payload_bytes: int = DEFAULT_MAX_PAYLOAD_BYTES,
        cleanup_interval_seconds: float = DEFAULT_CLEANUP_INTERVAL_SECONDS,
        monotonic: Callable[[], float] = time.monotonic,
    ):
        self._database = database
        self._max_age_seconds = max_age_seconds
        self._max_rows = max_rows
        self._max_payload_bytes = max_payload_bytes
        self._cleanup_interval_seconds = cleanup_interval_seconds
        self._monotonic = monotonic
        self._last_cleanup_at: Optional[float] = None
        self._lock = Lock()

    def get(self, source: str, key: str) -> Optional[SourceSnapshot]:
        with self._database.connection() as connection:
            row = connection.execute(
                """
                SELECT payload, captured_at
                  FROM source_snapshot
                 WHERE source = %s AND query_key = %s
                """,
                (source, key),
            ).fetchone()

        if row is None:
            return None

        games = _games_from_payload(row[0])

        if games is None:
            return None

        return SourceSnapshot(games=games, captured_at=row[1])

    def put(
        self,
        source: str,
        key: str,
        games: List[Game],
        captured_at: datetime,
    ) -> None:
        payload = _payload_from_games(games)

        # Una respuesta enorme no se guarda: el respaldo no debe crecer
        # sin control por una sola búsqueda.
        if len(json.dumps(payload)) > self._max_payload_bytes:
            return

        with self._database.connection() as connection:
            connection.execute(
                """
                INSERT INTO source_snapshot
                            (source, query_key, payload, captured_at)
                     VALUES (%s, %s, %s, %s)
                ON CONFLICT (source, query_key) DO UPDATE
                        SET payload = EXCLUDED.payload,
                            captured_at = EXCLUDED.captured_at
                """,
                (source, key, Jsonb(payload), captured_at),
            )

            if self._cleanup_is_due():
                self._cleanup(connection)

    def _cleanup_is_due(self) -> bool:
        now = self._monotonic()

        with self._lock:
            if (
                self._last_cleanup_at is not None
                and now - self._last_cleanup_at < self._cleanup_interval_seconds
            ):
                return False

            self._last_cleanup_at = now
            return True

    def _cleanup(self, connection) -> None:
        connection.execute(
            """
            DELETE FROM source_snapshot
             WHERE captured_at < now() - make_interval(secs => %s)
            """,
            (self._max_age_seconds,),
        )
        connection.execute(
            """
            DELETE FROM source_snapshot
             WHERE (source, query_key) IN (
                   SELECT source, query_key
                     FROM source_snapshot
                    ORDER BY captured_at DESC
                   OFFSET %s
             )
            """,
            (self._max_rows,),
        )


def _payload_from_games(games: List[Game]) -> list:
    return [
        {
            "id": game.id,
            "name": game.name,
            "prices": game.prices,
            "image": game.image,
            "links": game.links,
            "discounts": game.discounts,
        }
        for game in games
    ]


def _games_from_payload(payload) -> Optional[List[Game]]:
    """Una fila con forma inesperada cuenta como «sin respaldo»."""

    try:
        return [
            Game(
                id=item["id"],
                name=item["name"],
                prices=dict(item["prices"]),
                image=item.get("image"),
                links=dict(item.get("links") or {}),
                # Las copias guardadas antes de este campo no lo traen.
                discounts=dict(item.get("discounts") or {}),
            )
            for item in payload
        ]
    except (TypeError, KeyError, ValueError, AttributeError):
        return None
