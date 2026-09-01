from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_search_games_vertical_slice():
    response = client.get("/games/search?q=Minecraft")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "Minecraft"
    assert data[0]["prices"]["Steam"] == 29.99
    assert data[0]["prices"]["PlayStation"] == 29.99
    assert data[0]["prices"]["Xbox"] == 19.99