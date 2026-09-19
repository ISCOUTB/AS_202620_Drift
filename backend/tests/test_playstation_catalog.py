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
