import httpx

from app.infrastructure.external.cheapshark import cheapshark_game_repository
from app.infrastructure.external.cheapshark.cheapshark_game_repository import (
    CheapSharkGameRepository,
)
from app.infrastructure.persistence.combined_game_repository import (
    CombinedGameRepository,
)
from app.infrastructure.persistence.in_memory_game_repository import (
    InMemoryGameRepository,
)
from app.domain.model.game import Game
from app.domain.ports.exchange_rate_provider import ExchangeRateProvider


class _FixedExchangeRate(ExchangeRateProvider):
    def usd_to_cop(self) -> float:
        return 4000.0


class _MockResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def _mock_cheapshark(monkeypatch, calls=None):
    def mock_get(url, params=None, headers=None, timeout=None):
        if calls is not None:
            calls.append(url)

        if url.endswith("/deals"):
            assert params["title"] == "Portal 2"
            assert "DRIFT" in headers["User-Agent"]

            return _MockResponse([
                {
                    "title": "Portal 2",
                    "storeID": "1",
                    "gameID": "36",
                    "steamAppID": "620",
                    "salePrice": "9.99",
                },
                {
                    "title": "Portal 2",
                    "storeID": "7",
                    "gameID": "36",
                    "steamAppID": "620",
                    "salePrice": "5.00",
                },
                {
                    "title": "Portal 2",
                    "storeID": "25",
                    "gameID": "36",
                    "steamAppID": "620",
                    "salePrice": "2.50",
                },
                {
                    "title": "Portal 2",
                    "storeID": "4",
                    "gameID": "36",
                    "steamAppID": "620",
                    "salePrice": "1.00",
                },
            ])

        if url.endswith("/stores"):
            return _MockResponse([
                {"storeID": "1", "storeName": "Steam", "isActive": 1},
                {"storeID": "4", "storeName": "Amazon", "isActive": 0},
                {"storeID": "7", "storeName": "GOG", "isActive": 1},
                {"storeID": "25", "storeName": "Epic Games Store", "isActive": 1},
            ])

        raise AssertionError(f"URL inesperada: {url}")

    monkeypatch.setattr(cheapshark_game_repository.httpx, "get", mock_get)


def test_cheapshark_returns_pc_store_prices_in_cop(monkeypatch):
    _mock_cheapshark(monkeypatch)

    games = CheapSharkGameRepository(_FixedExchangeRate()).search("Portal 2")

    assert len(games) == 1
    assert games[0].id == "620"
    assert games[0].name == "Portal 2"

    # Sin Steam (se consulta aparte) ni tiendas inactivas.
    assert games[0].prices == {
        "GOG": 20000.0,
        "Epic Games Store": 10000.0,
    }


def test_cheapshark_caches_repeated_searches(monkeypatch):
    calls = []
    _mock_cheapshark(monkeypatch, calls)

    repository = CheapSharkGameRepository(_FixedExchangeRate())
    repository.search("Portal 2")
    repository.search("portal 2 ")

    assert len(calls) == 2


def test_cheapshark_prices_are_merged_by_steam_id(monkeypatch):
    _mock_cheapshark(monkeypatch)

    class SteamStub(InMemoryGameRepository):
        def __init__(self):
            self.games = [
                Game(620, "Portal 2™", {"Steam": 24499.0}),
            ]

    repository = CombinedGameRepository(
        primary_repository=SteamStub(),
        secondary_repository=CheapSharkGameRepository(_FixedExchangeRate()),
    )

    games = repository.search("Portal 2")

    assert len(games) == 1
    assert games[0].prices == {
        "Steam": 24499.0,
        "GOG": 20000.0,
        "Epic Games Store": 10000.0,
    }


def test_search_survives_cheapshark_failure(monkeypatch):
    def failing_get(*args, **kwargs):
        raise httpx.ConnectError("CheapShark no disponible")

    monkeypatch.setattr(
        cheapshark_game_repository.httpx,
        "get",
        failing_get,
    )

    repository = CombinedGameRepository(
        primary_repository=InMemoryGameRepository(),
        secondary_repository=CheapSharkGameRepository(_FixedExchangeRate()),
    )

    games = repository.search("Minecraft")

    assert len(games) == 1
    assert games[0].prices["Steam"] == 119900.0
