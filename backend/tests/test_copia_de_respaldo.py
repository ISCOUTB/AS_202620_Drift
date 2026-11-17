"""
ADR-0015 — Copia de respaldo de cada fuente.

Si una fuente falla o se queda sin cuota, la búsqueda responde con lo último
que esa fuente entregó y lo avisa en `cached_sources`. Ninguna prueba usa la
red ni una base de datos: el reloj y las fuentes son simulados.
"""

import threading
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from fastapi.testclient import TestClient

from app import main
from app.domain.model.game import Game
from app.domain.model.source_snapshot import SourceSnapshot
from app.domain.ports.game_repository import GameRepository
from app.domain.ports.source_snapshot_store import SourceSnapshotStore
from app.infrastructure.external.resilient_http import ExternalSourceError
from app.infrastructure.external.single_flight_cache import SingleFlightCache
from app.infrastructure.external.steam import steam_game_repository
from app.infrastructure.observability import SearchMetrics
from app.infrastructure.persistence.combined_game_repository import (
    CombinedGameRepository,
)
from app.infrastructure.persistence.in_memory_source_snapshot_store import (
    InMemorySourceSnapshotStore,
)
from app.infrastructure.persistence.resilient_source_snapshot_store import (
    ResilientSourceSnapshotStore,
)
from app.infrastructure.persistence.stale_fallback_game_repository import (
    StaleFallbackGameRepository,
)
from tests.admin_auth import ADMIN_HEADERS

START = datetime(2026, 11, 12, 8, 0, tzinfo=timezone.utc)
FRESH = 15 * 60
STALE = 72 * 60 * 60


class Clock:
    def __init__(self):
        self.now = START

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += timedelta(seconds=seconds)


class ScriptedSource(GameRepository):
    """Fuente simulada: entrega cada resultado en orden y repite el último."""

    def __init__(self, *outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def search(self, query):
        self.calls.append(query)

        outcome = (
            self.outcomes.pop(0)
            if len(self.outcomes) > 1
            else self.outcomes[0]
        )

        if isinstance(outcome, Exception):
            raise outcome

        return outcome


def portal(price=24900.0):
    return [
        Game(
            id=620,
            name="Portal 2",
            prices={"GOG": price},
            links={"GOG": "https://example.test/portal-2"},
        )
    ]


def wrapped(source, clock, store=None):
    return StaleFallbackGameRepository(
        source,
        "CheapShark",
        store if store is not None else InMemorySourceSnapshotStore(),
        fresh_seconds=FRESH,
        stale_seconds=STALE,
        now=clock,
    )


SOURCE_FAILURES = [
    ExternalSourceError("CheapShark", "rate_limited", 429),
    ExternalSourceError("CheapShark", "timeout"),
    ExternalSourceError("CheapShark", "server_error", 503),
    httpx.ConnectError("sin conexión"),
]


# --- El envoltorio de una fuente ---------------------------------------------


def test_a_healthy_source_answers_itself_and_is_not_marked_as_cached():
    clock = Clock()
    repository = wrapped(ScriptedSource(portal()), clock)

    games = repository.search("Portal 2")

    assert games[0].prices == {"GOG": 24900.0}
    assert games[0].cached_sources == {}


def test_a_recent_copy_is_reused_without_calling_the_source():
    clock = Clock()
    source = ScriptedSource(portal())
    repository = wrapped(source, clock)

    repository.search("Portal 2")
    clock.advance(FRESH - 1)
    games = repository.search("  portal   2 ")

    # Ahorra cuota de la fuente: una sola llamada para las dos búsquedas.
    assert len(source.calls) == 1
    assert games[0].prices == {"GOG": 24900.0}
    assert games[0].cached_sources == {}


def test_after_the_fresh_window_the_source_is_called_again_and_the_copy_is_renewed():
    clock = Clock()
    source = ScriptedSource(portal(24900.0), portal(9900.0))
    repository = wrapped(source, clock)

    repository.search("Portal 2")
    clock.advance(FRESH + 1)
    games = repository.search("Portal 2")

    assert len(source.calls) == 2
    assert games[0].prices == {"GOG": 9900.0}
    assert games[0].cached_sources == {}

    # La copia renovada es la que se usa si después la fuente cae.
    source.outcomes = [ExternalSourceError("CheapShark", "timeout")]
    clock.advance(FRESH + 1)

    assert repository.search("Portal 2")[0].prices == {"GOG": 9900.0}


@pytest.mark.parametrize("failure", SOURCE_FAILURES)
def test_when_the_source_fails_the_last_copy_is_served_and_says_when_it_was_taken(
    failure,
):
    clock = Clock()
    source = ScriptedSource(portal(), failure)
    repository = wrapped(source, clock)

    repository.search("Portal 2")
    clock.advance(2 * 60 * 60)
    games = repository.search("Portal 2")

    assert games[0].prices == {"GOG": 24900.0}
    assert games[0].links == {"GOG": "https://example.test/portal-2"}
    assert games[0].cached_sources == {"CheapShark": START.isoformat()}


def test_a_copy_older_than_the_limit_is_not_served():
    clock = Clock()
    source = ScriptedSource(portal(), ExternalSourceError("CheapShark", "timeout"))
    repository = wrapped(source, clock)

    repository.search("Portal 2")
    clock.advance(STALE + 1)

    # Un precio de hace más de 72 h engaña más de lo que ayuda.
    with pytest.raises(ExternalSourceError):
        repository.search("Portal 2")


def test_without_a_copy_the_failure_is_reported_as_before():
    repository = wrapped(
        ScriptedSource(ExternalSourceError("CheapShark", "rate_limited", 429)),
        Clock(),
    )

    with pytest.raises(ExternalSourceError):
        repository.search("un juego que nadie buscó")


def test_an_empty_copy_is_not_presented_as_saved_data():
    clock = Clock()
    source = ScriptedSource([], ExternalSourceError("CheapShark", "timeout"))
    repository = wrapped(source, clock)

    assert repository.search("sin ofertas") == []
    clock.advance(FRESH + 1)

    with pytest.raises(ExternalSourceError):
        repository.search("sin ofertas")


def test_an_unexpected_error_is_not_hidden_behind_the_copy():
    clock = Clock()
    source = ScriptedSource(portal(), ValueError("error de programación"))
    repository = wrapped(source, clock)

    repository.search("Portal 2")
    clock.advance(FRESH + 1)

    with pytest.raises(ValueError):
        repository.search("Portal 2")


def test_served_copies_are_independent_from_the_stored_one():
    clock = Clock()
    source = ScriptedSource(portal(), ExternalSourceError("CheapShark", "timeout"))
    repository = wrapped(source, clock)

    repository.search("Portal 2")
    clock.advance(FRESH + 1)

    first = repository.search("Portal 2")
    first[0].prices["GOG"] = 1.0
    first[0].unavailable_sources.append("PlayStation")

    second = repository.search("Portal 2")

    assert second[0].prices == {"GOG": 24900.0}
    assert second[0].unavailable_sources == []


def test_last_known_reads_the_copy_without_calling_the_source():
    clock = Clock()
    source = ScriptedSource(portal())
    repository = wrapped(source, clock)

    assert repository.last_known("Portal 2") is None

    repository.search("Portal 2")
    clock.advance(60 * 60)
    games = repository.last_known("Portal 2")

    assert len(source.calls) == 1
    assert games[0].cached_sources == {"CheapShark": START.isoformat()}

    clock.advance(STALE)

    assert repository.last_known("Portal 2") is None


# --- La búsqueda combinada ----------------------------------------------------


class SteamOnly(GameRepository):
    def search(self, query):
        return [
            Game(id=620, name="Portal 2", prices={"Steam": 19900.0}),
            Game(id=400, name="Portal", prices={"Steam": 9900.0}),
        ]


def test_a_failed_source_with_a_copy_is_cached_and_not_unavailable():
    clock = Clock()
    source = ScriptedSource(
        portal(),
        ExternalSourceError("CheapShark", "rate_limited", 429),
    )
    cheapshark = wrapped(source, clock)
    repository = CombinedGameRepository(
        SteamOnly(),
        cheapshark,
        "CheapShark",
        timeout_seconds=2,
        secondary_last_known=cheapshark.last_known,
    )

    repository.search("Portal")
    clock.advance(60 * 60)
    games = repository.search("Portal")

    assert games[0].prices == {"Steam": 19900.0, "GOG": 24900.0}

    # El aviso va en todos los resultados de la búsqueda.
    for game in games:
        assert game.unavailable_sources == []
        assert game.cached_sources == {"CheapShark": START.isoformat()}


def test_a_source_that_exceeds_its_deadline_is_answered_from_its_copy():
    clock = Clock()
    release = threading.Event()

    class SlowSecondTime(GameRepository):
        def __init__(self):
            self.calls = 0

        def search(self, query):
            self.calls += 1

            if self.calls > 1:
                release.wait(timeout=5)

            return portal()

    cheapshark = wrapped(SlowSecondTime(), clock)
    repository = CombinedGameRepository(
        SteamOnly(),
        cheapshark,
        "CheapShark",
        timeout_seconds=0.05,
        secondary_last_known=cheapshark.last_known,
    )

    try:
        repository.search("Portal")
        clock.advance(60 * 60)
        games = repository.search("Portal")
    finally:
        release.set()

    assert games[0].prices == {"Steam": 19900.0, "GOG": 24900.0}
    assert games[0].unavailable_sources == []
    assert games[0].cached_sources == {"CheapShark": START.isoformat()}


def test_a_source_that_exceeds_its_deadline_without_a_copy_is_unavailable():
    release = threading.Event()

    class Slow(GameRepository):
        def search(self, query):
            release.wait(timeout=5)
            return []

    cheapshark = wrapped(Slow(), Clock())
    repository = CombinedGameRepository(
        SteamOnly(),
        cheapshark,
        "CheapShark",
        timeout_seconds=0.05,
        secondary_last_known=cheapshark.last_known,
    )

    try:
        games = repository.search("Portal")
    finally:
        release.set()

    assert games[0].unavailable_sources == ["CheapShark"]
    assert games[0].cached_sources == {}


# --- Los almacenes de copias --------------------------------------------------


def test_in_memory_store_is_bounded_and_drops_the_least_recently_used():
    store = InMemorySourceSnapshotStore(max_entries=2)

    store.put("Steam", "a", portal(), START)
    store.put("Steam", "b", portal(), START)
    store.get("Steam", "a")
    store.put("Steam", "c", portal(), START)

    assert store.get("Steam", "a") is not None
    assert store.get("Steam", "b") is None
    assert store.get("Steam", "c") is not None


class BrokenStore(SourceSnapshotStore):
    """Almacén duradero caído: toda operación falla."""

    def __init__(self):
        self.calls = 0
        self.broken = True
        self.saved = {}

    def get(self, source, key):
        self.calls += 1

        if self.broken:
            raise ConnectionError("base de datos caída")

        return self.saved.get((source, key))

    def put(self, source, key, games, captured_at):
        self.calls += 1

        if self.broken:
            raise ConnectionError("base de datos caída")

        self.saved[(source, key)] = SourceSnapshot(games, captured_at)


def test_when_the_database_is_down_the_memory_copy_is_used_and_nothing_fails():
    ticks = [0.0]
    durable = BrokenStore()
    store = ResilientSourceSnapshotStore(
        primary=durable,
        fallback=InMemorySourceSnapshotStore(),
        cooldown_seconds=30,
        monotonic=lambda: ticks[0],
    )

    store.put("Steam", "portal 2", portal(), START)

    assert store.get("Steam", "portal 2").games[0].name == "Portal 2"
    assert store.is_degraded()

    # Mientras dura la pausa no se vuelve a llamar a la base caída: su
    # tiempo de espera no se le suma a cada búsqueda.
    calls_after_failure = durable.calls
    store.get("Steam", "portal 2")
    store.put("Steam", "otra", portal(), START)

    assert durable.calls == calls_after_failure


def test_the_database_is_used_again_after_the_pause():
    ticks = [0.0]
    durable = BrokenStore()
    store = ResilientSourceSnapshotStore(
        primary=durable,
        fallback=InMemorySourceSnapshotStore(),
        cooldown_seconds=30,
        monotonic=lambda: ticks[0],
    )

    store.put("Steam", "portal 2", portal(), START)
    durable.broken = False
    ticks[0] = 31.0

    store.put("Steam", "portal 2", portal(9900.0), START + timedelta(hours=1))

    assert not store.is_degraded()
    assert ("Steam", "portal 2") in durable.saved


def test_the_newest_copy_wins_between_database_and_memory():
    durable = BrokenStore()
    durable.broken = False
    memory = InMemorySourceSnapshotStore()
    store = ResilientSourceSnapshotStore(primary=durable, fallback=memory)

    durable.saved[("Steam", "portal 2")] = SourceSnapshot(portal(1.0), START)
    memory.put("Steam", "portal 2", portal(2.0), START + timedelta(minutes=5))

    assert store.get("Steam", "portal 2").games[0].prices == {"GOG": 2.0}

    durable.saved[("Steam", "portal 2")] = SourceSnapshot(
        portal(3.0),
        START + timedelta(minutes=10),
    )

    assert store.get("Steam", "portal 2").games[0].prices == {"GOG": 3.0}


# --- Métricas -----------------------------------------------------------------


def test_metrics_count_searches_answered_from_a_copy():
    metrics = SearchMetrics()

    metrics.record_search(10.0)
    metrics.record_search(12.0, (), ("CheapShark",))
    metrics.record_search(15.0, ("PlayStation",), ("CheapShark", "Steam"))

    snapshot = metrics.backup_snapshot()

    assert snapshot["total_searches"] == 3
    assert snapshot["backup_searches"] == 2
    assert snapshot["by_source"] == {"CheapShark": 2, "Steam": 1}

    # La métrica de E6 no cambia: solo cuenta fuentes sin respuesta.
    assert metrics.degradation_snapshot()["degraded_searches"] == 1


# --- Endpoint GET /games/search -----------------------------------------------

client = TestClient(main.app)

SEARCH_URL = "https://store.steampowered.com/api/storesearch/"


def _json(payload, status_code=200):
    return httpx.Response(
        status_code,
        json=payload,
        request=httpx.Request("GET", SEARCH_URL),
    )


def test_endpoint_serves_steam_from_its_copy_when_steam_stops_answering(
    monkeypatch,
):
    steam_is_down = {"value": False}

    def fake_get(url, params=None, **kwargs):
        if "store.steampowered.com" not in url:
            raise httpx.ConnectError("ruta no simulada")

        if steam_is_down["value"]:
            return _json({}, status_code=429)

        if "storesearch" in url:
            return _json({"items": [{"id": 620, "name": "Portal 2"}]})

        return _json(
            {
                "620": {
                    "data": {
                        "price_overview": {"final": 1990000},
                        "header_image": "https://example.test/portal-2.jpg",
                    }
                }
            }
        )

    clock = Clock()
    steam = main.steam_with_backup

    monkeypatch.setattr(steam_game_repository.httpx, "get", fake_get)
    monkeypatch.setattr(steam, "_now", clock)
    monkeypatch.setattr(steam._repository, "_cache", SingleFlightCache(60))

    healthy = client.get("/games/search?q=Portal 2 respaldo").json()

    assert healthy[0]["prices"] == {"Steam": 19900.0}
    assert healthy[0]["cached_sources"] == {}

    # Tres horas después Steam responde 429 (sin cuota) a todo.
    steam_is_down["value"] = True
    clock.advance(3 * 60 * 60)
    monkeypatch.setattr(steam._repository, "_cache", SingleFlightCache(60))

    degraded = client.get("/games/search?q=Portal 2 respaldo").json()

    assert degraded[0]["name"] == "Portal 2"
    assert degraded[0]["prices"] == {"Steam": 19900.0}
    assert degraded[0]["cached_sources"] == {"Steam": START.isoformat()}
    assert "Steam" not in degraded[0]["unavailable_sources"]

    backup = client.get("/metrics", headers=ADMIN_HEADERS).json()["source_backup"]

    assert backup["by_source"].get("Steam", 0) >= 1
