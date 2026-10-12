import httpx

from fastapi.testclient import TestClient

from app.infrastructure.external.playstation import playstation_game_catalog_source
from app.main import app, playstation_catalog


client = TestClient(app)


def test_sync_playstation_catalog_caches_the_single_provider_response(monkeypatch):
    def mock_get(url, params=None, headers=None, timeout=None):
        assert "STORE-MSF77008-ALLGAMES" in url
        assert params == {
            "size": 100,
            "start": 0,
            "gameContentType": "games",
        }
        assert headers == {"Accept": "application/json"}

        class MockResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return {
                    "links": [
                        {
                            "id": "UP0000-CUSA00000_00-DRIFTGAME000000",
                            "name": "Juego DRIFT",
                            "playable_platform": "PS4",
                            "default_sku": {
                                "price": 5990000,
                                "currency": "COP",
                                "discount": 20,
                            },
                        }
                    ]
                }

        return MockResponse()

    monkeypatch.setattr(playstation_game_catalog_source.httpx, "get", mock_get)

    response = client.post("/games/sync/playstation")

    assert response.status_code == 200
    assert response.json()["source"] == "playstation"
    assert response.json()["games_loaded"] == 1

    cached_games = playstation_catalog.search("drift")
    assert len(cached_games) == 1
    assert cached_games[0].prices == {"PlayStation": 59900.0}


def test_failed_playstation_sync_preserves_local_catalog(monkeypatch):
    playstation_catalog.replace([])

    def failing_get(*args, **kwargs):
        raise httpx.ConnectError("PSN no disponible")

    monkeypatch.setattr(playstation_game_catalog_source.httpx, "get", failing_get)

    response = client.post("/games/sync/playstation")

    assert response.status_code == 503
    assert response.json()["detail"]["source"] == "playstation"
    assert response.json()["detail"]["local_data_preserved"] is True


def test_playstation_usd_prices_are_converted_and_missing_prices_omitted(monkeypatch):
    from app.domain.model.game import Game
    from app.domain.ports.exchange_rate_provider import ExchangeRateProvider
    from app.infrastructure.external.playstation.playstation_game_catalog_source import (
        PlayStationGameCatalogSource,
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

    class FixedExchangeRate(ExchangeRateProvider):
        def usd_to_cop(self) -> float:
            return 4000.0

    class SteamStub(InMemoryGameRepository):
        def __init__(self):
            self.games = [
                Game(1091500, "Cyberpunk 2077", {"Steam": 199000.0}),
            ]

    def mock_get(url, params=None):
        class MockResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return {
                    "links": [
                        {
                            "id": "A",
                            "name": "Cyberpunk 2077",
                            "default_sku": {
                                "price": 0,
                                "display_price": "Gratuito",
                            },
                        },
                        {
                            "id": "B",
                            "name": "Cyberpunk 2077",
                            "default_sku": {
                                "price": 4999,
                                "display_price": "US$49.99",
                            },
                        },
                        {
                            "id": "C",
                            "name": "Cyberpunk 2077: Phantom Liberty",
                        },
                    ]
                }

        return MockResponse()

    monkeypatch.setattr(playstation_game_catalog_source.httpx, "get", mock_get)

    repository = CombinedGameRepository(
        primary_repository=SteamStub(),
        secondary_repository=InMemoryPlayStationCatalog(
            search_source=PlayStationGameCatalogSource(FixedExchangeRate()),
        ),
        secondary_name="PlayStation",
    )

    games = repository.search("Cyberpunk 2077")

    assert games[0].prices == {
        "Steam": 199000.0,
        "PlayStation": 199960.0,
    }
    assert games[1].name == "Cyberpunk 2077: Phantom Liberty"
    assert games[1].prices == {}
