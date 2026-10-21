"""
S12 — El endpoint de sincronización de PlayStation conserva el catálogo local
cuando la fuente falla o responde sin juegos utilizables (arc42 §8.13).

Ninguna prueba usa la red: `httpx.get` se reemplaza por respuestas simuladas.
"""

from datetime import datetime, timezone

import httpx
from fastapi.testclient import TestClient

from app.domain.model.normalized_game import NormalizedGame
from app.infrastructure.external.playstation import playstation_game_catalog_source
from app.main import app, playstation_catalog

client = TestClient(app)

CATALOG_URL_PART = "STORE-MSF77008-ALLGAMES"


def local_game():
    return NormalizedGame(
        id="local",
        name="Juego DRIFT local",
        source="playstation",
        platform="PS5",
        price=59900.0,
        currency="COP",
        discount=0,
        captured_at=datetime.now(timezone.utc),
    )


def respond(url, status_code=200, payload=None):
    return httpx.Response(
        status_code,
        json=payload,
        request=httpx.Request("GET", url),
    )


def test_a_response_without_usable_games_does_not_wipe_the_local_catalog(
    monkeypatch,
):
    playstation_catalog.replace([local_game()])

    def get(url, params=None, headers=None, timeout=None):
        # Otra forma de respuesta: sin `links` ni elementos con id y nombre.
        return respond(url, 200, {"mantenimiento": True})

    monkeypatch.setattr(playstation_game_catalog_source.httpx, "get", get)

    response = client.post("/games/sync/playstation")

    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail["source"] == "playstation"
    assert detail["reason"] == "empty_catalog"
    assert detail["http_status"] is None
    assert detail["local_data_preserved"] is True
    assert [g.name for g in playstation_catalog.search("drift")] == [
        "Juego DRIFT local"
    ]


def test_a_source_error_reports_its_http_status_and_keeps_the_local_catalog(
    monkeypatch,
):
    playstation_catalog.replace([local_game()])
    calls = []

    def get(url, params=None, headers=None, timeout=None):
        calls.append(url)

        return respond(url, 503, {})

    monkeypatch.setattr(playstation_game_catalog_source.httpx, "get", get)

    response = client.post("/games/sync/playstation")

    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail["http_status"] == 503
    assert detail["local_data_preserved"] is True
    # Un reintento acotado frente a un 5xx transitorio.
    assert len(calls) == 2
    assert [g.name for g in playstation_catalog.search("drift")] == [
        "Juego DRIFT local"
    ]
