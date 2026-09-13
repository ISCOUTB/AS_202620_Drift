import httpx
from fastapi.testclient import TestClient

from app.infrastructure.external.steam import steam_game_repository
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


def test_search_uses_fallback_when_steam_is_unavailable(monkeypatch):
    def failing_get(*args, **kwargs):
        raise httpx.ConnectError("Steam no disponible")

    monkeypatch.setattr(
        steam_game_repository.httpx,
        "get",
        failing_get,
    )

    response = client.get("/games/search?q=Minecraft")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "Minecraft"
    assert data[0]["prices"]["Xbox"] == 19.99
    assert data[0]["unavailable_sources"] == ["Steam"]