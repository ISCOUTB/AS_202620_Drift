from fastapi.testclient import TestClient

from app.main import app
from app.infrastructure.external.steam import steam_game_repository


client = TestClient(app)


def test_search_games_vertical_slice(monkeypatch):
    """
    Prueba el recorrido completo del corte vertical:

    HTTP → FastAPI → SearchGames → GameRepository
    → SteamGameRepository → respuesta simulada de Steam → JSON
    """

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

    # Reemplazamos temporalmente httpx.get por nuestra respuesta simulada
    monkeypatch.setattr(
        steam_game_repository.httpx,
        "get",
        mock_get
    )

    # Ejecutamos el sistema desde su punto de entrada HTTP
    response = client.get("/games/search?q=Portal 2")

    # Verificamos que la API respondió correctamente
    assert response.status_code == 200

    data = response.json()

    # Verificamos que el resultado atravesó correctamente el sistema
    assert len(data) == 1
    assert data[0]["id"] == 620
    assert data[0]["name"] == "Portal 2"
    assert data[0]["prices"]["Steam"] == 26.00
