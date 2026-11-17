"""
Lo que pide la ficha del problema sobre plataformas y descuentos:

- filtrar según las plataformas que tiene el usuario;
- comparar precios y descuentos entre tiendas;
- mostrar también los juegos que solo existen en una tienda de consola.

Ninguna prueba usa la red.
"""

from datetime import datetime, timezone

import httpx
import pytest
from fastapi.testclient import TestClient

from app import main
from app.application.usecases.search_games import SearchGames
from app.domain.model.game import Game
from app.domain.model.normalized_game import NormalizedGame
from app.domain.ports.exchange_rate_provider import ExchangeRateProvider
from app.domain.ports.game_repository import GameRepository
from app.domain.services.platforms import platform_of_store, platforms_of_stores
from app.infrastructure.external.cheapshark.cheapshark_game_repository import (
    CheapSharkGameRepository,
)
from app.infrastructure.external.playstation.playstation_game_catalog_source import (
    PlayStationGameCatalogSource,
)
from app.infrastructure.external.steam import steam_game_repository
from app.infrastructure.external.steam.steam_game_repository import (
    SteamGameRepository,
)
from app.infrastructure.persistence.combined_game_repository import (
    CombinedGameRepository,
)
from app.infrastructure.persistence.in_memory_playstation_catalog import (
    InMemoryPlayStationCatalog,
)

client = TestClient(main.app)


class FixedRate(ExchangeRateProvider):
    def usd_to_cop(self) -> float:
        return 4000.0


class Fixed(GameRepository):
    def __init__(self, games):
        self.games = games

    def search(self, query):
        return self.games


def elden_ring():
    return Game(
        id=1245620,
        name="ELDEN RING",
        prices={
            "Steam": 179000.0,
            "GOG": 185000.0,
            "PlayStation": 239960.0,
            "Xbox": 201900.0,
        },
        links={
            "Steam": "https://example.test/steam",
            "PlayStation": "https://example.test/ps",
            "Xbox": "https://example.test/xbox",
        },
        discounts={"Steam": 40, "Xbox": 10},
    )


# --- Plataformas ---------------------------------------------------------------


def test_each_store_sells_for_one_platform():
    assert platform_of_store("PlayStation") == "PlayStation"
    assert platform_of_store("Xbox") == "Xbox"

    # Cualquier otra tienda, incluidas las que se integren después, es de PC.
    for store in ("Steam", "GOG", "Epic Games Store", "Microsoft Store", "Nuuvem"):
        assert platform_of_store(store) == "PC"

    assert platforms_of_stores(["Xbox", "GOG", "Steam"]) == ["PC", "Xbox"]
    assert platforms_of_stores([]) == []


def test_a_game_lists_the_platforms_it_has_a_price_for():
    assert elden_ring().platforms == ["PC", "PlayStation", "Xbox"]
    assert Game(id=1, name="Sin precio", prices={}).platforms == []


def test_search_without_a_filter_returns_everything():
    games = SearchGames(Fixed([elden_ring()])).execute("elden ring")

    assert set(games[0].prices) == {"Steam", "GOG", "PlayStation", "Xbox"}


def test_filter_keeps_only_the_stores_of_the_chosen_platforms():
    games = SearchGames(Fixed([elden_ring()])).execute(
        "elden ring",
        platforms=["Xbox", "PlayStation"],
    )

    assert games[0].prices == {"PlayStation": 239960.0, "Xbox": 201900.0}
    assert set(games[0].links) == {"PlayStation", "Xbox"}
    assert games[0].discounts == {"Xbox": 10}
    assert games[0].platforms == ["PlayStation", "Xbox"]


def test_filter_omits_games_not_sold_for_those_platforms():
    only_pc = Game(id=620, name="Portal 2", prices={"Steam": 24499.0})

    games = SearchGames(Fixed([only_pc, elden_ring()])).execute(
        "x",
        platforms=["Xbox"],
    )

    assert [game.name for game in games] == ["ELDEN RING"]


def test_filter_does_not_change_the_games_of_other_searches():
    game = elden_ring()

    SearchGames(Fixed([game])).execute("elden ring", platforms=["PC"])

    assert set(game.prices) == {"Steam", "GOG", "PlayStation", "Xbox"}


# --- Descuentos ----------------------------------------------------------------


def _json(payload):
    return httpx.Response(
        200,
        json=payload,
        request=httpx.Request("GET", "https://example.test"),
    )


def test_steam_reports_its_discount(monkeypatch):
    def fake_get(url, params=None, **kwargs):
        if "storesearch" in url:
            return _json({"items": [{"id": 620, "name": "Portal 2"}]})

        return _json(
            {
                "620": {
                    "data": {
                        "price_overview": {
                            "final": 489900,
                            "discount_percent": 80,
                        }
                    }
                }
            }
        )

    monkeypatch.setattr(steam_game_repository.httpx, "get", fake_get)

    game = SteamGameRepository().search("portal 2 descuento")[0]

    assert game.prices == {"Steam": 4899.0}
    assert game.discounts == {"Steam": 80}


@pytest.mark.parametrize("discount", [0, None, "80", True, 250, -5])
def test_steam_ignores_a_missing_or_absurd_discount(monkeypatch, discount):
    def fake_get(url, params=None, **kwargs):
        if "storesearch" in url:
            return _json({"items": [{"id": 620, "name": "Portal 2"}]})

        return _json(
            {
                "620": {
                    "data": {
                        "price_overview": {
                            "final": 2449900,
                            "discount_percent": discount,
                        }
                    }
                }
            }
        )

    monkeypatch.setattr(steam_game_repository.httpx, "get", fake_get)

    game = SteamGameRepository().search(f"portal 2 sin descuento {discount}")[0]

    assert game.prices == {"Steam": 24499.0}
    assert game.discounts == {}


def test_cheapshark_reports_the_discount_of_the_cheapest_offer(monkeypatch):
    from app.infrastructure.external.cheapshark import cheapshark_game_repository

    def fake_get(url, params=None, **kwargs):
        if url.endswith("/stores"):
            return _json(
                [
                    {"storeID": "7", "storeName": "GOG", "isActive": 1},
                    {"storeID": "25", "storeName": "Epic Games Store", "isActive": 1},
                ]
            )

        return _json(
            [
                {
                    "title": "Portal 2",
                    "steamAppID": "620",
                    "gameID": "1",
                    "storeID": "7",
                    "salePrice": "5.00",
                    "savings": "49.6",
                    "dealID": "a",
                },
                {
                    "title": "Portal 2",
                    "steamAppID": "620",
                    "gameID": "1",
                    "storeID": "7",
                    "salePrice": "2.00",
                    "savings": "80.02",
                    "dealID": "b",
                },
                {
                    "title": "Portal 2",
                    "steamAppID": "620",
                    "gameID": "1",
                    "storeID": "25",
                    "salePrice": "9.99",
                    "savings": "0.000000",
                    "dealID": "c",
                },
            ]
        )

    monkeypatch.setattr(cheapshark_game_repository.httpx, "get", fake_get)

    game = CheapSharkGameRepository(FixedRate()).search("portal 2")[0]

    assert game.prices == {"GOG": 8000.0, "Epic Games Store": 39960.0}
    assert game.discounts == {"GOG": 80}


def ps_item(sku):
    return {
        "id": "UP0700-PPSA04610_00-ELDENRING0000000",
        "name": "ELDEN RING PS4 & PS5",
        "images": [{"type": 1, "url": "https://img.test/elden.png"}],
        "default_sku": sku,
    }


def normalize(sku):
    return PlayStationGameCatalogSource(FixedRate())._normalize(
        ps_item(sku),
        datetime(2026, 11, 12, tzinfo=timezone.utc),
    )


def test_playstation_keeps_the_regular_price_without_a_sale():
    game = normalize({"price": 5999, "display_price": "US$59.99"})

    assert game.price == 239960.0
    assert game.discount == 0
    assert game.image == "https://img.test/elden.png"


def test_playstation_uses_the_sale_price_open_to_everyone():
    game = normalize(
        {
            "price": 5999,
            "display_price": "US$59.99",
            "rewards": [
                {"price": 3599, "discount": 40, "isPlus": False},
            ],
        }
    )

    assert game.price == 143960.0
    assert game.discount == 40


def test_playstation_ignores_a_price_only_for_plus_subscribers():
    game = normalize(
        {
            "price": 5999,
            "display_price": "US$59.99",
            "rewards": [
                {"price": 2999, "discount": 50, "isPlus": True},
                "no es una oferta",
                {"price": "x", "discount": 10},
                {"price": 9999, "discount": 10},
            ],
        }
    )

    assert game.price == 239960.0
    assert game.discount == 0


def test_playstation_catalog_exposes_image_and_discount():
    catalog = InMemoryPlayStationCatalog()
    catalog.replace(
        [
            NormalizedGame(
                id="UP0700-ELDEN",
                name="ELDEN RING",
                source="playstation",
                platform="PlayStation",
                price=143960.0,
                currency="COP",
                discount=40,
                captured_at=datetime(2026, 11, 12, tzinfo=timezone.utc),
                image="https://img.test/elden.png",
            )
        ]
    )

    game = catalog.search("elden")[0]

    assert game.prices == {"PlayStation": 143960.0}
    assert game.discounts == {"PlayStation": 40}
    assert game.image == "https://img.test/elden.png"


def test_the_discount_follows_the_price_that_is_kept_when_stores_are_combined():
    steam = Fixed([Game(id=620, name="Portal 2", prices={"Steam": 24499.0})])
    playstation = Fixed(
        [
            Game(
                id="A",
                name="Portal 2",
                prices={"PlayStation": 80000.0},
                discounts={"PlayStation": 20},
            ),
            Game(id="B", name="Portal 2", prices={"PlayStation": 60000.0}),
        ]
    )

    game = CombinedGameRepository(steam, playstation, "PlayStation").search("x")[0]

    # Gana la edición más barata, que no está en oferta: no hereda el
    # descuento de la otra.
    assert game.prices == {"Steam": 24499.0, "PlayStation": 60000.0}
    assert game.discounts == {}


# --- Endpoint GET /games/search ------------------------------------------------


def console_only():
    return Game(
        id="UP0700-PPSA04610_00-ELDENRINGSOTEE00",
        name="ELDEN RING Shadow of the Erdtree Edition",
        prices={"PlayStation": 319960.0},
        links={"PlayStation": "https://example.test/ps-sote"},
    )


@pytest.fixture
def fixed_search(monkeypatch):
    monkeypatch.setattr(
        main.search_games,
        "repository",
        Fixed(
            [
                elden_ring(),
                console_only(),
                Game(id="9NOPRICE", name="Sin precio", prices={}),
                Game(id=400, name="Portal", prices={}),
            ]
        ),
    )


def test_endpoint_returns_platforms_and_discounts(fixed_search):
    data = client.get("/games/search?q=elden ring").json()

    assert data[0]["id"] == "1245620"
    assert data[0]["platforms"] == ["PC", "PlayStation", "Xbox"]
    assert data[0]["discounts"] == {"Steam": 40, "Xbox": 10}


def test_endpoint_shows_a_game_that_only_exists_in_a_console_store(fixed_search):
    data = client.get("/games/search?q=elden ring").json()
    by_name = {item["name"]: item for item in data}

    console = by_name["ELDEN RING Shadow of the Erdtree Edition"]

    # Conserva el identificador de su tienda: no es un juego de Steam.
    assert console["id"] == "UP0700-PPSA04610_00-ELDENRINGSOTEE00"
    assert console["platforms"] == ["PlayStation"]
    assert console["prices"] == {"PlayStation": 319960.0}

    # Sin precio y sin identificador de Steam no hay nada que mostrar; un
    # juego de Steam sin precio (gratuito o sin lanzar) sí se conserva.
    assert "Sin precio" not in by_name
    assert "Portal" in by_name


def test_endpoint_filters_by_one_or_several_platforms(fixed_search):
    xbox = client.get("/games/search?q=elden ring&platform=Xbox").json()

    assert [item["name"] for item in xbox] == ["ELDEN RING"]
    assert xbox[0]["prices"] == {"Xbox": 201900.0}
    assert xbox[0]["platforms"] == ["Xbox"]

    consoles = client.get(
        "/games/search?q=elden ring&platform=Xbox&platform=PlayStation"
    ).json()

    assert len(consoles) == 2
    assert consoles[0]["prices"] == {"PlayStation": 239960.0, "Xbox": 201900.0}


def test_endpoint_rejects_an_unknown_platform(fixed_search):
    response = client.get("/games/search?q=elden ring&platform=Switch")

    assert response.status_code == 422
