"""
ADR-0014 — Copias de respaldo en PostgreSQL.

Las pruebas que necesitan una base de datos real solo corren si existe la
variable `DRIFT_TEST_DATABASE_URL` (el CI la define con un PostgreSQL de
servicio). Sin ella se omiten. Usan una base que se pueda vaciar: borran la
tabla `source_snapshot` antes de cada prueba.

La prueba de «base de datos caída» no necesita ninguna base: apunta a un
puerto donde nadie escucha.
"""

import os
import time
from datetime import datetime, timedelta, timezone

import pytest

pytest.importorskip("psycopg")
pytest.importorskip("psycopg_pool")

from app.domain.model.game import Game  # noqa: E402
from app.infrastructure.persistence.in_memory_source_snapshot_store import (  # noqa: E402
    InMemorySourceSnapshotStore,
)
from app.infrastructure.persistence.postgres_database import (  # noqa: E402
    PostgresDatabase,
)
from app.infrastructure.persistence.postgres_source_snapshot_store import (  # noqa: E402
    PostgresSourceSnapshotStore,
)
from app.infrastructure.persistence.resilient_source_snapshot_store import (  # noqa: E402
    ResilientSourceSnapshotStore,
)

DATABASE_URL = os.getenv("DRIFT_TEST_DATABASE_URL", "").strip()

needs_database = pytest.mark.skipif(
    not DATABASE_URL,
    reason="DRIFT_TEST_DATABASE_URL no está definida",
)

NOW = datetime.now(timezone.utc).replace(microsecond=0)
STALE = 72 * 60 * 60


def portal(price=24900.0):
    return [
        Game(
            id=620,
            name="Portal 2",
            prices={"GOG": price, "Epic Games Store": 31000.5},
            image="https://example.test/portal-2.jpg",
            links={"GOG": "https://example.test/portal-2"},
        )
    ]


@pytest.fixture
def database():
    database = PostgresDatabase(DATABASE_URL, acquire_timeout_seconds=5)

    with database.connection() as connection:
        connection.execute("TRUNCATE source_snapshot")

    yield database

    database.close()


def _store(database, **options):
    return PostgresSourceSnapshotStore(
        database,
        max_age_seconds=STALE,
        **options,
    )


def _count(database):
    with database.connection() as connection:
        return connection.execute(
            "SELECT count(*) FROM source_snapshot"
        ).fetchone()[0]


@needs_database
def test_a_copy_survives_a_new_connection_pool(database):
    _store(database).put("CheapShark", "portal 2", portal(), NOW)

    # Otro pool: lo mismo que ve la API después de reiniciarse.
    restarted = PostgresDatabase(DATABASE_URL, acquire_timeout_seconds=5)

    try:
        snapshot = _store(restarted).get("CheapShark", "portal 2")
    finally:
        restarted.close()

    assert snapshot.captured_at == NOW
    assert snapshot.games[0].id == "620"
    assert snapshot.games[0].name == "Portal 2"
    assert snapshot.games[0].prices == {"GOG": 24900.0, "Epic Games Store": 31000.5}
    assert snapshot.games[0].image == "https://example.test/portal-2.jpg"
    assert snapshot.games[0].links == {"GOG": "https://example.test/portal-2"}


@needs_database
def test_a_missing_copy_is_none_and_sources_do_not_mix(database):
    store = _store(database)

    store.put("CheapShark", "portal 2", portal(), NOW)

    assert store.get("CheapShark", "half-life") is None
    assert store.get("Steam", "portal 2") is None


@needs_database
def test_a_new_copy_replaces_the_previous_one(database):
    store = _store(database)

    store.put("CheapShark", "portal 2", portal(24900.0), NOW)
    store.put("CheapShark", "portal 2", portal(9900.0), NOW + timedelta(minutes=20))

    snapshot = store.get("CheapShark", "portal 2")

    assert snapshot.games[0].prices["GOG"] == 9900.0
    assert snapshot.captured_at == NOW + timedelta(minutes=20)
    assert _count(database) == 1


@needs_database
def test_cleanup_removes_copies_that_are_too_old(database):
    store = _store(database, cleanup_interval_seconds=0)

    store.put("CheapShark", "vieja", portal(), NOW - timedelta(seconds=STALE + 60))
    store.put("CheapShark", "reciente", portal(), NOW)

    assert store.get("CheapShark", "vieja") is None
    assert store.get("CheapShark", "reciente") is not None


@needs_database
def test_cleanup_keeps_only_the_newest_rows(database):
    store = _store(database, max_rows=3, cleanup_interval_seconds=0)

    for minute in range(6):
        store.put(
            "CheapShark",
            f"juego {minute}",
            portal(),
            NOW - timedelta(minutes=10 - minute),
        )

    assert _count(database) == 3
    assert store.get("CheapShark", "juego 0") is None
    assert store.get("CheapShark", "juego 5") is not None


@needs_database
def test_an_oversized_answer_is_not_stored(database):
    store = _store(database, max_payload_bytes=50)

    store.put("CheapShark", "portal 2", portal(), NOW)

    assert _count(database) == 0


@needs_database
def test_a_row_with_an_unexpected_shape_counts_as_no_copy(database):
    with database.connection() as connection:
        connection.execute(
            """
            INSERT INTO source_snapshot (source, query_key, payload, captured_at)
            VALUES ('CheapShark', 'rota', '{"no": "es una lista de juegos"}', now())
            """
        )

    assert _store(database).get("CheapShark", "rota") is None


@needs_database
def test_the_schema_is_created_once_and_migrations_are_not_repeated(database):
    second = PostgresDatabase(DATABASE_URL, acquire_timeout_seconds=5)

    try:
        with second.connection() as connection:
            versions = [
                row[0]
                for row in connection.execute(
                    "SELECT version FROM schema_migrations ORDER BY version"
                )
            ]
    finally:
        second.close()

    assert versions == [1, 2, 3, 4, 5]


def test_with_the_database_down_the_search_keeps_its_memory_copy_and_does_not_wait():
    # En el puerto 1 de este equipo no escucha nadie.
    database = PostgresDatabase(
        "postgresql://drift:irrelevante@127.0.0.1:1/drift",
        acquire_timeout_seconds=0.25,
    )
    store = ResilientSourceSnapshotStore(
        primary=PostgresSourceSnapshotStore(database, max_age_seconds=STALE),
        fallback=InMemorySourceSnapshotStore(),
    )

    try:
        started_at = time.monotonic()

        store.put("CheapShark", "portal 2", portal(), NOW)
        snapshot = store.get("CheapShark", "portal 2")
        store.get("CheapShark", "otra búsqueda")

        elapsed = time.monotonic() - started_at
    finally:
        database.close()

    assert snapshot.games[0].name == "Portal 2"
    assert store.is_degraded()

    # Solo la primera operación espera a la base (0,25 s); las demás no.
    assert elapsed < 1.5
