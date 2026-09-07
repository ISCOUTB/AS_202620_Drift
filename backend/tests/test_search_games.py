from fastapi.testclient import TestClient

from app.main import app
from tests.steam_fixtures import mock_steam_search  # noqa: F401


client = TestClient(app)


def test_search_games_vertical_slice(mock_steam_search):
    """
    Prueba el recorrido completo del corte vertical:

    HTTP → FastAPI → SearchGames → GameRepository
    → SteamGameRepository → respuesta simulada de Steam → JSON
    """

    response = client.get("/games/search?q=Portal 2")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == 620
    assert data[0]["name"] == "Portal 2"
    assert data[0]["prices"]["Steam"] == 26.00