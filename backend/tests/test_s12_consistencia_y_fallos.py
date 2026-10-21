"""
S12 — Garantías de consistencia, política de invalidación y errores de las
fuentes secundarias (arc42 §8.13 y §8.14).

Ninguna prueba usa la red: `httpx.get` se reemplaza por respuestas simuladas
(objetos `httpx.Response` reales) y la espera entre reintentos se registra sin
dormir. Las pruebas del endpoint de sincronización están en
`test_s12_sync_playstation_endpoint.py`.
"""

import threading
import time
from datetime import datetime, timezone

import httpx
import pytest

from app.application.usecases.sync_playstation_catalog import (
    CatalogSyncRejected,
    SyncPlayStationCatalog,
)
from app.domain.model.game import Game
from app.domain.model.normalized_game import NormalizedGame
from app.domain.ports.exchange_rate_provider import ExchangeRateProvider
from app.domain.ports.game_catalog_source import GameCatalogSource
from app.domain.ports.game_repository import GameRepository
from app.infrastructure.external.cheapshark import cheapshark_game_repository
from app.infrastructure.external.cheapshark.cheapshark_game_repository import (
    CheapSharkGameRepository,
)
from app.infrastructure.external.exchange import open_exchange_rate_provider
from app.infrastructure.external.exchange.open_exchange_rate_provider import (
    FAILURE_BACKOFF_SECONDS,
    RATE_LIMITED_BACKOFF_SECONDS,
    OpenExchangeRateProvider,
)
from app.infrastructure.external.resilient_http import ExternalSourceError
from app.infrastructure.external.single_flight_cache import SingleFlightCache
from app.infrastructure.external.steam import steam_game_requirements_repository
from app.infrastructure.external.steam.steam_game_requirements_repository import (
    SteamGameRequirementsRepository,
)
from app.infrastructure.persistence.combined_game_repository import (
    CombinedGameRepository,
)
from app.infrastructure.persistence.in_memory_game_repository import (
    InMemoryGameRepository,
)
from app.infrastructure.persistence.in_memory_playstation_catalog import (
    InMemoryPlayStationCatalog,
)

DEALS_URL = "https://www.cheapshark.com/api/1.0/deals"


def http_response(url, status_code=200, payload=None, headers=None):
    return httpx.Response(
        status_code,
        json=payload,
        headers=headers,
        request=httpx.Request("GET", url),
    )


class FixedRate(ExchangeRateProvider):
    def usd_to_cop(self) -> float:
        return 4000.0


def ps_game(game_id, name):
    return NormalizedGame(
        id=game_id,
        name=name,
        source="playstation",
        platform="PS5",
        price=59900.0,
        currency="COP",
        discount=0,
        captured_at=datetime.now(timezone.utc),
    )


# --- Catálogo PlayStation: atomicidad dentro del proceso -------------------


class StubCatalogSource(GameCatalogSource):
    def __init__(self, games):
        self.games = games

    def fetch_catalog(self):
        return self.games


def test_sync_replaces_the_whole_catalog_with_the_new_snapshot():
    catalog = InMemoryPlayStationCatalog()
    catalog.replace([ps_game("old", "Drift Viejo")])

    result = SyncPlayStationCatalog(
        source=StubCatalogSource([ps_game("new", "Drift Nuevo")]),
        catalog=catalog,
    ).execute()

    assert result["games_loaded"] == 1
    assert [g.name for g in catalog.search("drift")] == ["Drift Nuevo"]


def test_sync_rejects_a_source_without_games_and_keeps_the_local_catalog():
    catalog = InMemoryPlayStationCatalog()
    catalog.replace([ps_game("old", "Drift Viejo")])

    with pytest.raises(CatalogSyncRejected) as raised:
        SyncPlayStationCatalog(
            source=StubCatalogSource([]),
            catalog=catalog,
        ).execute()

    assert raised.value.reason == "empty_catalog"
    assert [g.name for g in catalog.search("drift")] == ["Drift Viejo"]


def test_replace_is_atomic_for_concurrent_readers_inside_one_process():
    # Garantía: un lector ve el catálogo anterior completo o el nuevo completo,
    # nunca una mezcla ni un catálogo a medias. Vale solo dentro del proceso.
    catalog = InMemoryPlayStationCatalog()
    snapshot_a = [ps_game(f"a{i}", f"Game A {i}") for i in range(50)]
    snapshot_b = [ps_game(f"b{i}", f"Game B {i}") for i in range(50)]
    catalog.replace(snapshot_a)

    stop = threading.Event()
    mixed = []

    def writer():
        flip = True

        while not stop.is_set():
            catalog.replace(snapshot_b if flip else snapshot_a)
            flip = not flip

    def reader():
        for _ in range(300):
            names = [g.name for g in catalog.search("game")]
            letters = {name.split()[1] for name in names}

            if len(names) != 50 or len(letters) != 1:
                mixed.append(names)

    writer_thread = threading.Thread(target=writer)
    readers = [threading.Thread(target=reader) for _ in range(4)]
    writer_thread.start()

    for thread in readers:
        thread.start()

    for thread in readers:
        thread.join()

    stop.set()
    writer_thread.join()

    assert mixed == []


# --- Caché con TTL: frescura acotada, sin invalidación explícita -----------


def test_cached_value_is_not_refreshed_before_the_ttl_even_if_the_source_changes():
    # Política: no hay invalidación por evento; la frescura la acota el TTL.
    cache = SingleFlightCache(ttl_seconds=0.3)
    source = {"price": 100}

    assert cache.get_or_load("k", lambda: source["price"]) == 100

    source["price"] = 90
    assert cache.get_or_load("k", lambda: source["price"]) == 100

    time.sleep(0.35)
    assert cache.get_or_load("k", lambda: source["price"]) == 90


def test_a_failed_load_is_not_cached():
    cache = SingleFlightCache(ttl_seconds=60)
    attempts = []

    def failing():
        attempts.append(1)
        raise ExternalSourceError("Steam", "timeout")

    for _ in range(2):
        with pytest.raises(ExternalSourceError):
            cache.get_or_load("k", failing)

    assert len(attempts) == 2
    assert cache.get_or_load("k", lambda: "ok") == "ok"


# --- Tasa de cambio: respaldo y espera tras un fallo -----------------------


class StepClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def test_exchange_rate_does_not_hammer_the_source_during_the_failure_backoff(
    monkeypatch,
):
    clock, calls = StepClock(), []

    def failing_get(url, timeout=None):
        calls.append(url)

        raise httpx.ConnectError("sin red")

    monkeypatch.setattr(open_exchange_rate_provider.httpx, "get", failing_get)
    monkeypatch.setenv("USD_TO_COP_RATE", "3900")
    provider = OpenExchangeRateProvider(clock=clock)

    assert provider.usd_to_cop() == 3900.0
    assert provider.usd_to_cop() == 3900.0
    clock.now += FAILURE_BACKOFF_SECONDS - 1
    assert provider.usd_to_cop() == 3900.0
    assert len(calls) == 1

    clock.now += 2
    provider.usd_to_cop()
    assert len(calls) == 2


def test_exchange_rate_limited_response_backs_off_twenty_minutes(monkeypatch):
    clock, calls = StepClock(), []

    def limited_get(url, timeout=None):
        calls.append(url)

        return http_response(url, 429, {})

    monkeypatch.setattr(open_exchange_rate_provider.httpx, "get", limited_get)
    monkeypatch.setenv("USD_TO_COP_RATE", "3900")
    provider = OpenExchangeRateProvider(clock=clock)

    assert provider.usd_to_cop() == 3900.0

    clock.now += FAILURE_BACKOFF_SECONDS + 1
    provider.usd_to_cop()
    assert len(calls) == 1

    clock.now += RATE_LIMITED_BACKOFF_SECONDS
    provider.usd_to_cop()
    assert len(calls) == 2


def test_exchange_rate_serves_the_last_known_rate_when_a_refresh_fails(monkeypatch):
    # Limitación documentada: la tasa vencida se sigue sirviendo sin aviso.
    clock = StepClock()
    state = {"fail": False}

    def get(url, timeout=None):
        if state["fail"]:
            raise httpx.ConnectError("sin red")

        return http_response(url, 200, {"rates": {"COP": 4100}})

    monkeypatch.setattr(open_exchange_rate_provider.httpx, "get", get)
    provider = OpenExchangeRateProvider(clock=clock)

    assert provider.usd_to_cop() == 4100.0

    clock.now += 13 * 60 * 60
    state["fail"] = True

    assert provider.usd_to_cop() == 4100.0


# --- CheapShark: ausencia legítima frente a fallo --------------------------


def cheapshark_get(calls, deals_payload, stores_payload=None, deals_status=200, deals_headers=None):
    def get(url, params=None, headers=None, timeout=None):
        calls.append(url)

        if url.endswith("/deals"):
            return http_response(url, deals_status, deals_payload, deals_headers)

        if url.endswith("/stores"):
            payload = [{"storeID": "1", "storeName": "Steam", "isActive": 1}]

            return http_response(url, 200, stores_payload or payload)

        raise AssertionError(url)

    return get


def repository(sleeps=None):
    return CheapSharkGameRepository(
        FixedRate(),
        sleep=(sleeps if sleeps is not None else []).append,
    )


def test_cheapshark_empty_list_is_a_legitimate_result_and_is_cached(monkeypatch):
    calls = []
    monkeypatch.setattr(
        cheapshark_game_repository.httpx, "get", cheapshark_get(calls, [])
    )
    repo = repository()

    assert repo.search("zzz") == []
    assert repo.search("zzz") == []
    assert len(calls) == 1


def test_cheapshark_unexpected_shape_is_a_failure_and_is_not_cached(monkeypatch):
    calls = []
    monkeypatch.setattr(
        cheapshark_game_repository.httpx,
        "get",
        cheapshark_get(calls, {"error": "mantenimiento"}),
    )
    repo = repository()

    for _ in range(2):
        with pytest.raises(ExternalSourceError) as raised:
            repo.search("portal")

        assert raised.value.reason == "invalid_response"

    assert len(calls) == 2


def test_cheapshark_honours_retry_after_once_and_then_succeeds(monkeypatch):
    calls, sleeps = [], []
    outcomes = [
        http_response(DEALS_URL, 429, {}, {"Retry-After": "1"}),
        http_response(DEALS_URL, 200, []),
    ]

    def get(url, params=None, headers=None, timeout=None):
        calls.append(url)

        return outcomes.pop(0)

    monkeypatch.setattr(cheapshark_game_repository.httpx, "get", get)

    assert repository(sleeps).search("portal") == []
    assert len(calls) == 2
    assert sleeps == [1.0]


def test_cheapshark_does_not_retry_a_permanent_4xx(monkeypatch):
    calls, sleeps = [], []
    monkeypatch.setattr(
        cheapshark_game_repository.httpx,
        "get",
        cheapshark_get(calls, {}, deals_status=404),
    )

    with pytest.raises(ExternalSourceError) as raised:
        repository(sleeps).search("portal")

    assert raised.value.reason == "client_error"
    assert len(calls) == 1
    assert sleeps == []


def test_cheapshark_gives_up_after_the_limited_retries_on_5xx(monkeypatch):
    calls, sleeps = [], []
    monkeypatch.setattr(
        cheapshark_game_repository.httpx,
        "get",
        cheapshark_get(calls, {}, deals_status=503),
    )

    with pytest.raises(ExternalSourceError) as raised:
        repository(sleeps).search("portal")

    assert raised.value.reason == "server_error"
    assert len(calls) == 2


def test_cheapshark_keeps_serving_with_the_stale_store_list_if_refresh_fails(
    monkeypatch,
):
    deals = [{
        "title": "Portal 2",
        "storeID": "7",
        "gameID": "36",
        "steamAppID": "620",
        "salePrice": "10.00",
    }]

    def get(url, params=None, headers=None, timeout=None):
        if url.endswith("/deals"):
            return http_response(url, 200, deals)

        raise httpx.ConnectError("tiendas no disponibles")

    monkeypatch.setattr(cheapshark_game_repository.httpx, "get", get)
    repo = repository()
    repo._stores = {"7": "GOG"}
    repo._stores_loaded_at = time.monotonic() - 25 * 60 * 60  # vencida

    games = repo.search("portal 2")

    assert games[0].prices == {"GOG": 40000.0}


def test_cheapshark_without_any_store_list_reports_the_failure(monkeypatch):
    deals = [{"title": "Portal 2", "storeID": "7", "salePrice": "10.00"}]

    def get(url, params=None, headers=None, timeout=None):
        if url.endswith("/deals"):
            return http_response(url, 200, deals)

        raise httpx.ConnectError("tiendas no disponibles")

    monkeypatch.setattr(cheapshark_game_repository.httpx, "get", get)

    with pytest.raises(ExternalSourceError):
        repository().search("portal 2")


# --- Fuentes secundarias en la búsqueda combinada --------------------------


class RaisingRepository(GameRepository):
    def __init__(self, error):
        self.error = error

    def search(self, query):
        raise self.error


@pytest.mark.parametrize(
    "error",
    [
        ExternalSourceError("CheapShark", "timeout"),
        ExternalSourceError("CheapShark", "rate_limited", 429),
        ExternalSourceError("CheapShark", "server_error", 503),
        ExternalSourceError("CheapShark", "invalid_response"),
    ],
)
def test_combined_search_reports_a_typed_source_failure_without_failing(error):
    combined = CombinedGameRepository(
        primary_repository=InMemoryGameRepository(),
        secondary_repository=RaisingRepository(error),
        secondary_name="CheapShark",
    )

    games = combined.search("Minecraft")

    assert len(games) == 1
    assert games[0].unavailable_sources == ["CheapShark"]


# --- Requisitos de Steam: el fallo no se guarda en la caché ----------------

REQUIREMENTS_PAYLOAD = {
    "7": {
        "success": True,
        "data": {
            "pc_requirements": {
                "minimum": "<ul><li><strong>Memoria:</strong> 4 GB de RAM</li></ul>"
            }
        },
    }
}


def test_steam_requirements_failure_is_not_cached_and_recovers(monkeypatch):
    state = {"calls": 0}

    def get(url, params=None, timeout=None):
        state["calls"] += 1

        if state["calls"] == 1:
            raise httpx.ConnectError("Steam no disponible")

        return http_response(url, 200, REQUIREMENTS_PAYLOAD)

    monkeypatch.setattr(steam_game_requirements_repository.httpx, "get", get)
    repo = SteamGameRequirementsRepository()

    assert repo.get_by_game_id(7) is None
    assert repo.get_by_game_id(7).minimum_ram_gb == 4
    assert state["calls"] == 2


def test_steam_requirements_unexpected_shape_is_not_reported_as_empty(monkeypatch):
    def get(url, params=None, timeout=None):
        return http_response(url, 200, ["no", "es", "un", "objeto"])

    monkeypatch.setattr(steam_game_requirements_repository.httpx, "get", get)

    assert SteamGameRequirementsRepository().get_by_game_id(7) is None
