from fastapi.testclient import TestClient

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


def test_compatibility_reports_missing_requirements():
    response = client.post(
        "/games/999999/compatibility",
        json={
            "ram_gb": 8,
            "gpu_score": 3,
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Requisitos no disponibles"