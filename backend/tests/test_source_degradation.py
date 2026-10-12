import threading
import time

import httpx
from fastapi.testclient import TestClient

from app.domain.model.game import Game
from app.domain.ports.game_repository import GameRepository
from app.infrastructure.external.single_flight_cache import SingleFlightCache
from app.infrastructure.external.steam import steam_game_repository
from app.infrastructure.external.steam.steam_game_repository import (
    SteamGameRepository,
)
from app.infrastructure.persistence.combined_game_repository import (
    CombinedGameRepository,
)
from app.infrastructure.persistence.in_memory_game_repository import (
    InMemoryGameRepository,
)


class _PrimaryStub(GameRepository):
    def search(self, query):
        return [Game(620, "Portal 2", {"Steam": 24499.0})]


class _SlowSource(GameRepository):
    """Fuente que responde bien, pero después del plazo."""

    def __init__(self, delay_seconds):
        self.delay_seconds = delay_seconds

    def search(self, query):
        time.sleep(self.delay_seconds)
        return [Game(620, "Portal 2", {"GOG": 20000.0})]


class _FailingSource(GameRepository):
    def search(self, query):
        raise httpx.ConnectError("fuente no disponible")


def test_slow_source_is_abandoned_at_the_deadline_and_reported():
    repository = CombinedGameRepository(
        primary_repository=_PrimaryStub(),
        secondary_repository=_SlowSource(delay_seconds=1.0),
        secondary_name="CheapShark",
        timeout_seconds=0.2,
    )

    started_at = time.monotonic()
    games = repository.search("Portal 2")
    elapsed_seconds = time.monotonic() - started_at

    # No esperó el segundo completo de la fuente lenta.
    assert elapsed_seconds < 0.8
    assert games[0].prices == {"Steam": 24499.0}
    assert games[0].unavailable_sources == ["CheapShark"]


def test_failing_source_is_reported():
    repository = CombinedGameRepository(
        primary_repository=_PrimaryStub(),
        secondary_repository=_FailingSource(),
        secondary_name="PlayStation",
        timeout_seconds=1.0,
    )

    games = repository.search("Portal 2")

    assert games[0].prices == {"Steam": 24499.0}
    assert games[0].unavailable_sources == ["PlayStation"]


def test_source_within_the_deadline_is_merged_without_notice():
    repository = CombinedGameRepository(
        primary_repository=_PrimaryStub(),
        secondary_repository=_SlowSource(delay_seconds=0.05),
        secondary_name="CheapShark",
        timeout_seconds=1.0,
    )

    games = repository.search("Portal 2")

    assert games[0].prices == {"Steam": 24499.0, "GOG": 20000.0}
    assert games[0].unavailable_sources == []


def test_single_flight_cache_loads_each_key_once_under_concurrency():
    cache = SingleFlightCache(ttl_seconds=60)
    calls = []

    def loader():
        calls.append(1)
        time.sleep(0.1)
        return "valor"

    results = []
    threads = [
        threading.Thread(
            target=lambda: results.append(cache.get_or_load("clave", loader))
        )
        for _ in range(8)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert results == ["valor"] * 8
    assert len(calls) == 1


def test_single_flight_cache_does_not_block_other_keys_nor_cache_errors():
    cache = SingleFlightCache(ttl_seconds=60)
    slow_started = threading.Event()
    release_slow = threading.Event()

    def slow_loader():
        slow_started.set()
        release_slow.wait(timeout=5)
        return "lenta"

    slow_thread = threading.Thread(
        target=lambda: cache.get_or_load("lenta", slow_loader)
    )
    slow_thread.start()
    assert slow_started.wait(timeout=5)

    # Con la carga lenta todavía en curso, otra clave responde de inmediato.
    started_at = time.monotonic()
    assert cache.get_or_load("rapida", lambda: "rapida") == "rapida"
    assert time.monotonic() - started_at < 0.5

    release_slow.set()
    slow_thread.join()

    attempts = []

    def failing_then_ok():
        attempts.append(1)

        if len(attempts) == 1:
            raise httpx.ConnectError("fallo temporal")

        return "recuperada"

    try:
        cache.get_or_load("inestable", failing_then_ok)
    except httpx.ConnectError:
        pass

    # El error no quedó en caché: el segundo intento vuelve a consultar.
    assert cache.get_or_load("inestable", failing_then_ok) == "recuperada"


def test_notice_does_not_leak_into_cached_or_stored_games(monkeypatch):
    def mock_get(url, params=None, **kwargs):
        class MockResponse:
            def raise_for_status(self):
                pass

            def json(self):
                if "storesearch" in url:
                    return {"items": [{"id": 620, "name": "Portal 2"}]}

                return {"620": {"data": {"price_overview": {"final": 2449900}}}}

        return MockResponse()

    monkeypatch.setattr(steam_game_repository.httpx, "get", mock_get)

    steam = SteamGameRepository()

    degraded = CombinedGameRepository(
        primary_repository=steam,
        secondary_repository=_FailingSource(),
        secondary_name="CheapShark",
        timeout_seconds=1.0,
    ).search("Portal 2")

    assert degraded[0].unavailable_sources == ["CheapShark"]

    # La siguiente lectura de la caché de Steam no arrastra el aviso anterior.
    assert steam.search("Portal 2")[0].unavailable_sources == []

    fallback = InMemoryGameRepository()
    fallback.search("Minecraft")[0].prices["GOG"] = 1.0

    assert "GOG" not in fallback.search("Minecraft")[0].prices


def test_metrics_expose_degraded_searches_by_source(monkeypatch):
    from app.main import app

    def failing_get(*args, **kwargs):
        raise httpx.ConnectError("sin red")

    monkeypatch.setattr(steam_game_repository.httpx, "get", failing_get)

    client = TestClient(app)

    before = client.get("/metrics").json()["source_degradation"]

    assert client.get("/games/search?q=Minecraft").status_code == 200

    after = client.get("/metrics").json()["source_degradation"]

    assert after["metric"] == "drift_source_unavailable_total"
    assert after["degraded_searches"] == before["degraded_searches"] + 1
    assert (
        after["by_source"]["CheapShark"]
        == before["by_source"].get("CheapShark", 0) + 1
    )
