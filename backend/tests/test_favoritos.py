"""
ADR-0020 — Juegos favoritos de quien inicia sesión.

Reutiliza el proveedor de identidad simulado y los almacenes de
`test_cuentas.py`: memoria siempre y PostgreSQL si existe
`DRIFT_TEST_DATABASE_URL`.
"""

from datetime import timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.application.usecases.accounts import (
    Devices,
    FavoriteNotFound,
    Favorites,
    Sessions,
)
from app.domain.model.account import (
    MAX_FAVORITES_PER_USER,
    Favorite,
    InvalidFavorite,
)
from app.infrastructure.api.account_routes import (
    AccountSettings,
    build_account_router,
)
from app.infrastructure.persistence.in_memory_account_repository import (
    InMemoryAccountRepository,
)
from tests.test_cuentas import (  # noqa: F401  `accounts` es un fixture
    ANA,
    LUIS,
    NOW,
    ORIGIN,
    TRUSTED,
    FakeGoogle,
    accounts,
    sign_in,
)

IMAGE = "https://cdn.example.test/steam/apps/620/library_600x900.jpg"


def favorite(user, game_id="620", name="Portal 2", minutes=0, **changes):
    values = {
        "user_id": user.id,
        "game_id": game_id,
        "name": name,
        "image": IMAGE,
        "price": 24_500.0,
        "store": "Steam",
        "saved_at": NOW + timedelta(minutes=minutes),
    }
    values.update(changes)

    return Favorite(**values)


# --- El almacén (memoria y, si hay base de datos, PostgreSQL) ------------------


def test_favorites_belong_to_their_owner_and_come_newest_first(accounts):
    ana = accounts.save_user(ANA)
    luis = accounts.save_user(LUIS)

    accounts.save_favorite(favorite(ana, "620", "Portal 2"))
    accounts.save_favorite(favorite(ana, "itad-abc", "Hades", minutes=5))
    accounts.save_favorite(favorite(luis, "620", "Portal 2"))

    saved = accounts.list_favorites(ana.id)

    assert [item.game_id for item in saved] == ["itad-abc", "620"]
    assert saved[1] == favorite(ana, "620", "Portal 2")
    assert saved[1].price == 24_500.0
    assert saved[1].saved_at == NOW

    assert accounts.delete_favorite(luis.id, "itad-abc") is False
    assert accounts.delete_favorite(ana.id, "itad-abc") is True
    assert [item.game_id for item in accounts.list_favorites(ana.id)] == ["620"]
    assert len(accounts.list_favorites(luis.id)) == 1


def test_saving_a_favorite_again_replaces_it(accounts):
    ana = accounts.save_user(ANA)

    accounts.save_favorite(favorite(ana))
    accounts.save_favorite(
        favorite(ana, price=None, store=None, image=None, minutes=10)
    )

    saved = accounts.list_favorites(ana.id)

    assert len(saved) == 1
    assert (saved[0].price, saved[0].store, saved[0].image) == (None, None, None)
    assert saved[0].saved_at == NOW + timedelta(minutes=10)


def test_deleting_an_account_removes_its_favorites(accounts):
    ana = accounts.save_user(ANA)
    luis = accounts.save_user(LUIS)

    accounts.save_favorite(favorite(ana))
    accounts.save_favorite(favorite(luis))

    accounts.delete_user(ana.id)

    assert accounts.list_favorites(ana.id) == []
    assert len(accounts.list_favorites(luis.id)) == 1


# --- Las reglas ----------------------------------------------------------------


@pytest.mark.parametrize(
    "changes",
    [
        {"game_id": "../etc"},
        {"game_id": ""},
        {"name": "   "},
        {"name": "x" * 201},
        {"image": "http://sin-https.test/a.jpg"},
        {"image": "javascript:alert(1)"},
        {"image": "https://img.test/a.jpg');background:url('x"},
        {"image": "https://img.test/" + "a" * 500},
        {"price": -1},
        {"price": True},
        {"price": 10, "store": None},
        {"price": None, "store": "Steam"},
        {"store": " "},
    ],
)
def test_invalid_favorites_are_rejected(changes):
    ana = InMemoryAccountRepository().save_user(ANA)

    with pytest.raises(InvalidFavorite):
        favorite(ana, **changes)


def test_a_user_cannot_save_favorites_without_limit():
    repository = InMemoryAccountRepository()
    ana = repository.save_user(ANA)
    favorites = Favorites(repository, now=lambda: NOW)

    for number in range(MAX_FAVORITES_PER_USER):
        favorites.save(ana, f"juego-{number}", "Un juego")

    with pytest.raises(InvalidFavorite):
        favorites.save(ana, "uno-mas", "Otro juego")

    # Volver a guardar uno que ya estaba sí se permite.
    assert favorites.save(ana, "juego-0", "Un juego", price=10, store="GOG").price == 10

    with pytest.raises(FavoriteNotFound):
        favorites.remove(ana, "no-esta")


# --- La API --------------------------------------------------------------------


@pytest.fixture
def api():
    repository = InMemoryAccountRepository()
    app = FastAPI()
    app.include_router(
        build_account_router(
            Sessions(repository, FakeGoogle()),
            Devices(repository),
            AccountSettings(ORIGIN, [ORIGIN], secure_cookies=False),
            Favorites(repository),
        )
    )

    return TestClient(app, follow_redirects=False)


BODY = {"name": "Portal 2", "image": IMAGE, "price": 24_500, "store": "Steam"}


def test_favorites_need_a_session(api):
    assert api.get("/favorites").status_code == 401
    assert api.put("/favorites/620", json=BODY, headers=TRUSTED).status_code == 401
    assert api.delete("/favorites/620", headers=TRUSTED).status_code == 401


def test_a_user_saves_lists_and_removes_favorites(api):
    sign_in(api)

    saved = api.put("/favorites/620", json=BODY, headers=TRUSTED)

    assert saved.status_code == 200
    assert saved.json()["game_id"] == "620"
    assert saved.json()["price"] == 24_500
    assert saved.json()["saved_at"]

    api.put("/favorites/itad-abc", json={"name": "Hades"}, headers=TRUSTED)

    listed = api.get("/favorites").json()

    assert {item["game_id"] for item in listed} == {"620", "itad-abc"}
    assert set(listed[0]) == {
        "game_id",
        "name",
        "image",
        "price",
        "store",
        "saved_at",
        "target_price",
    }

    assert api.delete("/favorites/620", headers=TRUSTED).json() == {"deleted": True}
    assert api.delete("/favorites/620", headers=TRUSTED).status_code == 404
    assert [item["game_id"] for item in api.get("/favorites").json()] == ["itad-abc"]


def test_one_user_does_not_see_the_favorites_of_another(api):
    sign_in(api, "ana")
    api.put("/favorites/620", json=BODY, headers=TRUSTED)

    api.cookies.clear()
    sign_in(api, "luis")

    assert api.get("/favorites").json() == []
    assert api.delete("/favorites/620", headers=TRUSTED).status_code == 404


@pytest.mark.parametrize(
    "path, body",
    [
        ("/favorites/620", {}),
        ("/favorites/620", {"name": "Portal 2", "price": -5, "store": "Steam"}),
        ("/favorites/620", {"name": "Portal 2", "price": 10}),
        ("/favorites/620", {"name": "Portal 2", "image": "http://x.test/a.jpg"}),
        ("/favorites/con%20espacio", {"name": "Portal 2"}),
    ],
)
def test_invalid_favorites_are_refused_by_the_api(api, path, body):
    sign_in(api)

    assert api.put(path, json=body, headers=TRUSTED).status_code == 422


def test_alerts_is_not_a_game_that_can_be_saved(api):
    # Sin la ruta reservada, PUT /favorites/alerts guardaba un favorito «alerts».
    sign_in(api)

    for method in ("put", "delete"):
        answer = getattr(api, method)("/favorites/alerts", headers=TRUSTED)

        assert answer.status_code == 405
        assert answer.headers["allow"] == "GET"

    assert api.get("/favorites").json() == []


def test_method_not_allowed_lists_every_method_of_the_address():
    # Contrato: `Allow` lista todos los métodos de /auth/me, no solo los de
    # la primera ruta que coincide.
    from app.main import app as drift_app

    answer = TestClient(drift_app).request("OPTIONS", "/auth/me")

    assert answer.status_code == 405
    assert set(answer.headers["allow"].split(", ")) == {"GET", "DELETE"}


def test_favorite_changes_from_another_site_are_refused(api):
    sign_in(api)

    for headers in ({}, {"Origin": "https://otro-sitio.test"}):
        assert api.put("/favorites/620", json=BODY, headers=headers).status_code == 403
        assert api.delete("/favorites/620", headers=headers).status_code == 403


def test_a_failing_store_answers_unavailable(api, monkeypatch):
    sign_in(api)

    def broken(*args, **kwargs):
        raise ConnectionError("base de datos caída")

    monkeypatch.setattr(InMemoryAccountRepository, "list_favorites", broken)

    response = api.get("/favorites")

    assert response.status_code == 503
    assert response.json()["detail"]["reason"] == "accounts_unavailable"


def test_without_login_configured_there_are_no_favorites():
    app = FastAPI()
    app.include_router(
        build_account_router(
            None, None, AccountSettings(ORIGIN, [ORIGIN], secure_cookies=False)
        )
    )

    assert TestClient(app).get("/favorites").status_code == 404
