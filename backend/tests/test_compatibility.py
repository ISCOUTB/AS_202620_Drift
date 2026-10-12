from fastapi.testclient import TestClient

from app.infrastructure.external.steam import steam_game_requirements_repository
from app.main import app

client = TestClient(app)


def test_compatibility_is_compatible_with_recommended_specs():
    response = client.post(
        "/games/620/compatibility",
        json={
            "ram_gb": 8,
            "gpu_score": 3,
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Compatible"


def test_compatibility_has_limitations_with_minimum_specs():
    response = client.post(
        "/games/620/compatibility",
        json={
            "ram_gb": 2,
            "gpu_score": 1,
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Compatible con limitaciones"


def test_compatibility_is_not_compatible_below_minimum_specs():
    response = client.post(
        "/games/620/compatibility",
        json={
            "ram_gb": 1,
            "gpu_score": 1,
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "No compatible"


def test_compatibility_reports_missing_requirements(monkeypatch):
    # Steam tampoco conoce el juego; se simula para no depender de la red.
    class NoGameResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"999999": {"success": False}}

    monkeypatch.setattr(
        steam_game_requirements_repository.httpx,
        "get",
        lambda *args, **kwargs: NoGameResponse(),
    )

    response = client.post(
        "/games/999999/compatibility",
        json={
            "ram_gb": 8,
            "gpu_score": 3,
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Requisitos no disponibles"