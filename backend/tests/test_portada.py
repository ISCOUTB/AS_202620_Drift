"""
Lo que muestra la portada además de la búsqueda: los juegos más vendidos del
momento (por categoría) y la lista de tiendas conectadas.

Ninguna prueba usa la red.
"""

import httpx
import pytest
from fastapi.testclient import TestClient

from app import main
from app.application.usecases.showcase import ListFeaturedGames, ListStores
from app.domain.ports.showcase import FeaturedGame, PcStoreDirectory
from app.infrastructure.external.resilient_http import RetryPolicy
from app.infrastructure.external.single_flight_cache import SingleFlightCache
from app.infrastructure.external.steam import steam_featured_games_source
from app.infrastructure.external.steam.steam_featured_games_source import (
    SteamFeaturedGamesSource,
)

client = TestClient(main.app)

POLICY = RetryPolicy(timeout_seconds=3.0, max_attempts=1)


def logo(app_id):
    return (
        "https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/"
        f"{app_id}/abc123/capsule_sm_120.jpg?t=1"
    )


def _response(payload):
    return httpx.Response(
        200,
        json=payload,
        request=httpx.Request("GET", "https://example.test"),
    )


@pytest.fixture
def steam_search(monkeypatch):
    state = {"outcome": None, "calls": []}

    def fake_get(url, params=None, **kwargs):
        state["calls"].append(params)

        if isinstance(state["outcome"], Exception):
            raise state["outcome"]

        return state["outcome"]

    monkeypatch.setattr(steam_featured_games_source.httpx, "get", fake_get)

    return state


def source():
    return SteamFeaturedGamesSource(policy=POLICY, sleep=lambda _: None)


# --- Juegos del momento --------------------------------------------------------


def test_top_sellers_come_with_the_images_built_from_their_steam_id(steam_search):
    steam_search["outcome"] = _response(
        {
            "items": [
                {"name": "Forza Horizon 6", "logo": logo(2483190)},
                {"name": "iRacing", "logo": logo(266410)},
                # Repetido, sin identificador reconocible o con otra forma.
                {"name": "Forza Horizon 6", "logo": logo(2483190)},
                {"name": "Paquete", "logo": "https://example.test/sub/1/x.jpg"},
                {"name": "", "logo": logo(1)},
                "no es un juego",
            ]
        }
    )

    games = source().list("Carreras")

    assert [game.name for game in games] == ["Forza Horizon 6", "iRacing"]
    assert games[0].id == "2483190"
    assert games[0].image.endswith("/2483190/library_600x900.jpg")
    assert games[0].hero.endswith("/2483190/library_hero.jpg")
    assert games[0].header.endswith("/2483190/header.jpg")

    params = steam_search["calls"][0]

    # Etiqueta de «Carreras», solo juegos y la tienda de Colombia.
    assert params["tags"] == 699
    assert params["category1"] == 998
    assert params["cc"] == "co"


def test_the_general_list_is_asked_without_a_tag_and_reused_for_an_hour(
    steam_search,
):
    steam_search["outcome"] = _response(
        {"items": [{"name": "Counter-Strike 2", "logo": logo(730)}]}
    )
    featured = source()

    featured.list(None)
    featured.list(None)

    assert len(steam_search["calls"]) == 1
    assert "tags" not in steam_search["calls"][0]


def test_when_steam_fails_the_last_list_is_served_and_never_an_error(steam_search):
    steam_search["outcome"] = _response(
        {"items": [{"name": "Counter-Strike 2", "logo": logo(730)}]}
    )
    featured = source()

    assert len(featured.list(None)) == 1

    # Vence la hora de caché y Steam ya no responde.
    featured._cache = SingleFlightCache(ttl_seconds=3600)
    steam_search["outcome"] = httpx.ConnectError("Steam caído")

    assert [game.name for game in featured.list(None)] == ["Counter-Strike 2"]

    # Una categoría que nunca se obtuvo queda vacía: la portada usa su respaldo.
    assert featured.list("RPG") == []


@pytest.mark.parametrize("payload", [{}, {"items": []}, {"items": "x"}, []])
def test_an_empty_or_strange_answer_does_not_replace_the_last_list(
    steam_search, payload
):
    steam_search["outcome"] = _response(
        {"items": [{"name": "Counter-Strike 2", "logo": logo(730)}]}
    )
    featured = source()
    featured.list(None)

    featured._cache = SingleFlightCache(ttl_seconds=3600)
    steam_search["outcome"] = _response(payload)

    assert [game.name for game in featured.list(None)] == ["Counter-Strike 2"]


def test_use_case_rejects_an_unknown_category():
    class Empty:
        def list(self, category):
            return []

    with pytest.raises(ValueError):
        ListFeaturedGames(Empty()).execute("Terror")

    assert ListFeaturedGames(Empty()).execute("Aventura") == []
    assert ListFeaturedGames(Empty()).execute(None) == []


def test_featured_endpoint(monkeypatch):
    class Fixed:
        def list(self, category):
            return [
                FeaturedGame(
                    id="730",
                    name=f"Juego de {category}",
                    image="https://img.test/p.jpg",
                    hero="https://img.test/h.jpg",
                    header="https://img.test/c.jpg",
                )
            ]

    monkeypatch.setattr(main.list_featured_games, "source", Fixed())

    data = client.get("/games/featured?category=Aventura").json()

    assert data["category"] == "Aventura"
    assert data["items"] == [
        {
            "id": "730",
            "name": "Juego de Aventura",
            "image": "https://img.test/p.jpg",
            "hero": "https://img.test/h.jpg",
            "header": "https://img.test/c.jpg",
        }
    ]
    assert client.get("/games/featured").json()["category"] is None
    assert client.get("/games/featured?category=Terror").status_code == 422


# --- Tiendas -------------------------------------------------------------------


class Directory(PcStoreDirectory):
    def __init__(self, names=None, error=None):
        self.names = names or []
        self.error = error

    def pc_stores(self):
        if self.error:
            raise self.error

        return self.names


def test_stores_list_direct_stores_first_and_then_the_pc_stores_in_order():
    answer = ListStores(
        Directory(["GOG", "Fanatical", "epic Game Store", "GOG", "Steam"]),
        "IsThereAnyDeal",
    ).execute()

    assert answer["complete"] is True
    assert [store["name"] for store in answer["items"]] == [
        "Steam",
        "PlayStation",
        "Xbox",
        "Microsoft Store",
        "epic Game Store",
        "Fanatical",
        "GOG",
    ]

    by_name = {store["name"]: store for store in answer["items"]}

    assert by_name["PlayStation"]["platform"] == "PlayStation"
    assert by_name["Xbox"]["platform"] == "Xbox"
    assert by_name["GOG"] == {
        "name": "GOG",
        "platform": "PC",
        "source": "IsThereAnyDeal",
    }


def test_when_the_directory_fails_the_direct_stores_are_still_listed():
    answer = ListStores(
        Directory(error=ConnectionError("fuente caída")),
        "IsThereAnyDeal",
    ).execute()

    assert answer["complete"] is False
    assert [store["name"] for store in answer["items"]] == [
        "Steam",
        "PlayStation",
        "Xbox",
        "Microsoft Store",
    ]


def test_stores_endpoint(monkeypatch):
    monkeypatch.setattr(main.list_stores, "directory", Directory(["GOG"]))

    data = client.get("/stores").json()

    assert data["complete"] is True
    assert data["items"][-1]["name"] == "GOG"
    assert len(data["items"]) == 5
