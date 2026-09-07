import pytest

from app.infrastructure.external.steam import steam_game_repository


class _MockSteamResponse:
    """Respuesta simulada equivalente a `httpx.Response` para los tests."""

    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


@pytest.fixture
def mock_steam_search(monkeypatch):
    """Simula la búsqueda de 'Portal 2' en la API pública de Steam."""

    def mock_get(url, params=None):
        if "storesearch" in url:
            return _MockSteamResponse({
                "items": [
                    {"id": 620, "name": "Portal 2"}
                ]
            })

        if "appdetails" in url:
            return _MockSteamResponse({
                "620": {
                    "success": True,
                    "data": {
                        "price_overview": {"final": 2600}
                    }
                }
            })

        return _MockSteamResponse({})

    monkeypatch.setattr(steam_game_repository.httpx, "get", mock_get)
