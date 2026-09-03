from fastapi.testclient import TestClient

from app.main import app
from app.infrastructure.external.steam import steam_game_repository


client = TestClient(app)


def test_health():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_search_games_vertical_slice(monkeypatch):
    def mock_get(url, params=None):
        class MockResponse:
            def raise_for_status(self):
                pass

            def json(self):
                if "storesearch" in url:
                    return {
                        "items": [
                            {
                                "id": 620,
                                "name": "Portal 2"
                            }
                        ]
                    }

                if "appdetails" in url:
                    return {
                        "620": {
                            "success": True,
                            "data": {
                                "price_overview": {
                                    "final": 2600
                                }
                            }
                        }
                    }

                return {}

        return MockResponse()

    monkeypatch.setattr(
        steam_game_repository.httpx,
        "get",
        mock_get
    )

    response = client.get("/games/search?q=Portal 2")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == 620
    assert data[0]["name"] == "Portal 2"
    assert data[0]["prices"]["Steam"] == 26.00