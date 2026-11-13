"""
ADR-0021 — Alertas de precio de los favoritos.

Ninguna prueba usa la red: Steam e IsThereAnyDeal son dobles de prueba.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.application.usecases.accounts import Devices, Favorites, Sessions
from app.application.usecases.favorite_alerts import MAX_CHECKED, CheckFavoriteAlerts
from app.domain.model.account import Favorite, InvalidFavorite
from app.domain.ports.current_price_source import CurrentPriceSource
from app.domain.services.price_alerts import (
    PRICE_DROPPED,
    TARGET_REACHED,
    CurrentPrice,
    price_alert,
)
from app.infrastructure.api.account_routes import AccountSettings, build_account_router
from app.infrastructure.external import store_current_prices
from app.infrastructure.external.resilient_http import ExternalSourceError
from app.infrastructure.external.store_current_prices import StoreCurrentPriceSource
from app.infrastructure.persistence.in_memory_account_repository import (
    InMemoryAccountRepository,
)
from tests.test_cuentas import ANA, NOW, ORIGIN, TRUSTED, FakeGoogle, sign_in

ITAD_PORTAL = "01849783-6a26-7147-ab32-71804ca47e8e"
ITAD_HADES = "018d937f-11e6-715a-a82e-a2ef0bd4d8ad"


# --- La regla ------------------------------------------------------------------


def test_a_target_price_alerts_when_today_is_at_or_below_it():
    today = CurrentPrice("GOG", 40_000)

    alert = price_alert(saved_price=60_000, target_price=40_000, current=today)

    assert alert.reason == TARGET_REACHED
    assert alert.saved_difference == 20_000
    assert price_alert(60_000, 39_999, today) is None


def test_with_a_target_a_small_drop_does_not_alert():
    # Bajó 30 %, pero la persona pidió que le avisaran a 30.000.
    assert price_alert(60_000, 30_000, CurrentPrice("Steam", 42_000)) is None


def test_without_a_target_it_alerts_on_a_drop_of_five_percent_or_more():
    assert price_alert(100_000, None, CurrentPrice("Steam", 95_000)).reason == (
        PRICE_DROPPED
    )
    # Un cambio por la tasa de cambio del día no avisa.
    assert price_alert(100_000, None, CurrentPrice("GOG", 96_000)) is None
    assert price_alert(100_000, None, CurrentPrice("GOG", 120_000)) is None


def test_without_price_today_or_reference_there_is_no_alert():
    assert price_alert(100_000, 50_000, None) is None
    assert price_alert(None, None, CurrentPrice("Steam", 10)) is None
    # Sin precio guardado, el objetivo sí puede avisar.
    alert = price_alert(None, 20, CurrentPrice("Steam", 10))

    assert alert.reason == TARGET_REACHED
    assert alert.saved_difference is None


@pytest.mark.parametrize("target", [0, -5, True, "10", 2_000_000_000])
def test_invalid_targets_are_rejected(target):
    with pytest.raises(InvalidFavorite):
        Favorite(user_id="u", game_id="620", name="Portal 2", target_price=target)


# --- El caso de uso ------------------------------------------------------------


class Prices(CurrentPriceSource):
    def __init__(self, prices=None, error=None):
        self.prices = prices or {}
        self.error = error
        self.asked = []

    def best_prices(self, game_ids):
        self.asked.append(list(game_ids))

        if self.error:
            raise self.error

        return {game_id: self.prices[game_id] for game_id in game_ids if game_id in self.prices}


def setup(prices):
    repository = InMemoryAccountRepository()
    ana = repository.save_user(ANA)
    favorites = Favorites(repository, now=lambda: NOW)

    return repository, ana, favorites, CheckFavoriteAlerts(repository, prices, now=lambda: NOW)


def test_each_favorite_gets_todays_price_and_its_alert():
    prices = Prices(
        {
            "620": CurrentPrice("Steam", 20_000),
            "itad-x": CurrentPrice("GOG", 99_000),
        }
    )
    _, ana, favorites, alerts = setup(prices)

    favorites.save(ana, "620", "Portal 2", price=30_000, store="Steam")
    favorites.save(ana, "itad-x", "Hades", price=100_000, store="GOG")
    favorites.save(ana, "PPSA01-ABC", "Solo PS5", price=200_000, store="PlayStation")

    answer = alerts.execute(ana)

    by_id = {status.favorite.game_id: status for status in answer.statuses}

    assert answer.alerts == 1
    assert by_id["620"].alert.reason == PRICE_DROPPED
    assert by_id["itad-x"].alert is None
    assert by_id["PPSA01-ABC"].current is None
    assert answer.checked_at == NOW


def test_saving_a_favorite_again_keeps_its_target():
    _, ana, favorites, _ = setup(Prices())

    favorites.save(ana, "620", "Portal 2", price=30_000, store="Steam")
    favorites.set_target(ana, "620", 15_000)
    saved = favorites.save(ana, "620", "Portal 2", price=28_000, store="Steam")

    assert saved.target_price == 15_000
    assert saved.price == 28_000
    assert favorites.set_target(ana, "620", None).target_price is None


def test_only_the_most_recent_favorites_are_checked():
    prices = Prices()
    _, ana, favorites, alerts = setup(prices)

    for number in range(MAX_CHECKED + 5):
        favorites.save(ana, f"{number}", "Un juego")

    alerts.execute(ana)

    assert len(prices.asked[0]) == MAX_CHECKED


def test_when_the_price_source_fails_favorites_still_come_without_price():
    _, ana, favorites, alerts = setup(Prices(error=RuntimeError("todo caído")))

    favorites.save(ana, "620", "Portal 2", price=30_000, store="Steam")

    answer = alerts.execute(ana)

    assert answer.alerts == 0
    assert answer.statuses[0].current is None


# --- El adaptador de precios ---------------------------------------------------


class FakeItad:
    def __init__(self, lookup=None, prices=None, error=None):
        self.lookup = lookup or {}
        self.prices = prices or []
        self.error = error
        self.calls = []

    def new_budget(self, seconds=None):
        return None

    def post(self, path, body, params=None, budget=None):
        self.calls.append((path, body))

        if self.error:
            raise self.error

        if path.startswith("/lookup"):
            return self.lookup

        return self.prices


class Rates:
    def usd_to_cop(self):
        return 4_000


def itad_entry(itad_id, *deals):
    return {
        "id": itad_id,
        "deals": [
            {"shop": {"name": store}, "price": {"amount": usd, "currency": "USD"}, "cut": 0}
            for store, usd in deals
        ],
    }


def steam(prices):
    calls = []

    def lookup(app_id):
        calls.append(app_id)
        found = prices.get(app_id)

        if isinstance(found, Exception):
            raise found

        return found

    lookup.calls = calls

    return lookup


def test_the_cheapest_store_wins_between_steam_and_the_other_pc_stores():
    itad = FakeItad(
        lookup={"app/620": ITAD_PORTAL},
        prices=[
            itad_entry(ITAD_PORTAL, ("GOG", 4), ("Fanatical", 5)),
            itad_entry(ITAD_HADES, ("Humble Store", 10)),
        ],
    )
    source = StoreCurrentPriceSource(
        steam({"620": (30_000, 24_500, 0)}), itad, Rates()
    )

    prices = source.best_prices(["620", f"itad-{ITAD_HADES}", "PPSA01-ABC"])

    assert prices["620"] == CurrentPrice("GOG", 16_000)
    assert prices[f"itad-{ITAD_HADES}"] == CurrentPrice("Humble Store", 40_000)
    assert "PPSA01-ABC" not in prices

    # Dos llamadas a IsThereAnyDeal para todos los juegos juntos.
    assert [path for path, _ in itad.calls] == [
        "/lookup/id/shop/61/v1",
        "/games/prices/v3",
    ]
    assert sorted(itad.calls[1][1]) == sorted([ITAD_PORTAL, ITAD_HADES])


def test_prices_are_reused_for_an_hour():
    clock = {"now": 0.0}
    steam_prices = steam({"620": (30_000, 24_500, 0)})
    source = StoreCurrentPriceSource(steam_prices, clock=lambda: clock["now"])

    source.best_prices(["620"])
    source.best_prices(["620"])
    clock["now"] = store_current_prices.TTL_SECONDS + 1
    source.best_prices(["620"])

    assert steam_prices.calls == ["620", "620"]


def test_when_itad_fails_steam_still_answers():
    itad = FakeItad(error=ExternalSourceError("IsThereAnyDeal", "rate_limited"))
    source = StoreCurrentPriceSource(steam({"620": (30_000, 24_500, 0)}), itad, Rates())

    assert source.best_prices(["620", f"itad-{ITAD_HADES}"]) == {
        "620": CurrentPrice("Steam", 24_500)
    }


def test_when_every_source_fails_the_failure_is_not_remembered():
    steam_prices = steam({"620": ConnectionError("Steam caído")})
    source = StoreCurrentPriceSource(steam_prices)

    assert source.best_prices(["620"]) == {}

    steam_prices_ok = {"620": (30_000, 24_500, 0)}
    source._steam_prices = steam(steam_prices_ok)

    assert source.best_prices(["620"]) == {"620": CurrentPrice("Steam", 24_500)}


def test_a_strange_answer_from_itad_is_ignored():
    itad = FakeItad(lookup="no es un objeto")
    source = StoreCurrentPriceSource(steam({}), itad, Rates())

    assert source.best_prices(["620"]) == {}


# --- La API --------------------------------------------------------------------


@pytest.fixture
def api():
    repository = InMemoryAccountRepository()
    prices = Prices({"620": CurrentPrice("Steam", 9_000)})
    app = FastAPI()
    app.include_router(
        build_account_router(
            Sessions(repository, FakeGoogle()),
            Devices(repository),
            AccountSettings(ORIGIN, [ORIGIN], secure_cookies=False),
            Favorites(repository),
            CheckFavoriteAlerts(repository, prices),
        )
    )

    return TestClient(app, follow_redirects=False)


def test_alerts_need_a_session(api):
    assert api.get("/favorites/alerts").status_code == 401
    assert (
        api.put("/favorites/620/target", json={"target_price": 10}, headers=TRUSTED)
        .status_code
        == 401
    )


def test_a_user_sets_a_target_and_gets_alerted(api):
    sign_in(api)

    api.put(
        "/favorites/620",
        json={"name": "Portal 2", "price": 24_500, "store": "Steam"},
        headers=TRUSTED,
    )

    target = api.put(
        "/favorites/620/target", json={"target_price": 10_000}, headers=TRUSTED
    )

    assert target.status_code == 200
    assert target.json()["target_price"] == 10_000
    assert api.get("/favorites").json()[0]["target_price"] == 10_000

    answer = api.get("/favorites/alerts").json()

    assert answer["alerts"] == 1
    assert answer["checked_at"]
    assert answer["items"] == [
        {
            "game_id": "620",
            "current": {"store": "Steam", "price": 9_000},
            "alert": {"reason": "target_reached", "saved_difference": 15_500},
        }
    ]

    # Quitar el objetivo: queda la regla de la baja del 5 %, que también aplica.
    api.put("/favorites/620/target", json={"target_price": None}, headers=TRUSTED)

    assert api.get("/favorites/alerts").json()["items"][0]["alert"]["reason"] == (
        "price_dropped"
    )


@pytest.mark.parametrize(
    "path, body, status",
    [
        ("/favorites/620/target", {"target_price": 0}, 422),
        ("/favorites/620/target", {"target_price": -1}, 422),
        ("/favorites/no-esta/target", {"target_price": 10}, 404),
    ],
)
def test_invalid_targets_are_refused(api, path, body, status):
    sign_in(api)
    api.put("/favorites/620", json={"name": "Portal 2"}, headers=TRUSTED)

    assert api.put(path, json=body, headers=TRUSTED).status_code == status


def test_target_changes_from_another_site_are_refused(api):
    sign_in(api)
    api.put("/favorites/620", json={"name": "Portal 2"}, headers=TRUSTED)

    response = api.put(
        "/favorites/620/target",
        json={"target_price": 10},
        headers={"Origin": "https://otro-sitio.test"},
    )

    assert response.status_code == 403


def test_the_real_app_limits_the_rate_of_alert_checks():
    from app import main

    class Request:
        method = "GET"

        class url:
            path = "/favorites/alerts"

    assert main._calls_external_sources(Request) is True
