"""
Página «Explorar»: el catálogo de Steam por género, etiquetas, orden y precio,
con la ficha de cada juego, y las imágenes reales de la portada.

Ninguna prueba usa la red.
"""

import json
from datetime import date

import httpx
import pytest
from fastapi.testclient import TestClient

from app import main
from app.application.usecases.showcase import ExploreGames
from app.domain.ports.showcase import ExploreGame, ExplorePage, ExploreQuery
from app.infrastructure.external.resilient_http import RetryPolicy
from app.infrastructure.external.steam import (
    steam_featured_games_source,
    steam_game_explorer,
    steam_store_items,
)
from app.infrastructure.external.steam.steam_featured_games_source import (
    SteamFeaturedGamesSource,
)
from app.infrastructure.external.steam.steam_game_explorer import SteamGameExplorer
from app.infrastructure.external.steam.steam_store_items import SteamStoreItems

POLICY = RetryPolicy(timeout_seconds=3.0, max_attempts=1)

client = TestClient(main.app)


def _response(payload, status=200):
    return httpx.Response(
        status,
        json=payload,
        request=httpx.Request("GET", "https://example.test"),
    )


def logo(app_id):
    return (
        "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/"
        f"{app_id}/abc/capsule_sm_120.jpg?t=1"
    )


def store_item(app_id, name, **changes):
    item = {
        "success": 1,
        "appid": app_id,
        "name": name,
        "assets": {
            "asset_url_format": f"steam/apps/{app_id}/${{FILENAME}}?t=9",
            "library_capsule": "c0de/library_capsule.jpg",
            "library_hero": "beef/library_hero.jpg",
            "header": "f00d/header.jpg",
            "main_capsule": "cafe/capsule_616x353.jpg",
        },
        "basic_info": {
            "short_description": "Un juego de prueba.",
            "developers": [{"name": "Estudio A"}, {"name": "Estudio B"}, {"name": "C"}],
        },
        "tags": [
            {"tagid": 19, "weight": 500},
            {"tagid": 122, "weight": 900},
            {"tagid": 99999, "weight": 950},
        ],
        "release": {"steam_release_date": 1745871301},
        "reviews": {
            "summary_filtered": {"review_score_label": "Muy positivas", "percent_positive": 91}
        },
        "best_purchase_option": {
            "final_price_in_cents": "1699000",
            "original_price_in_cents": "16990000",
            "discount_pct": 90,
        },
    }
    item.update(changes)

    return item


TAG_LIST = {"response": {"tags": [{"tagid": 19, "name": "Acción"}, {"tagid": 122, "name": "Rol"}]}}


@pytest.fixture
def steam(monkeypatch):
    """Simula la búsqueda de la tienda, GetItems y la lista de etiquetas."""

    state = {"search": [], "items": [], "calls": [], "fail": set()}

    def fake_get(url, params=None, **kwargs):
        state["calls"].append((url, params))

        for name in state["fail"]:
            if name in url:
                raise httpx.ConnectError("Steam caído")

        if "GetTagList" in url:
            return _response(TAG_LIST)

        if "GetItems" in url:
            wanted = {entry["appid"] for entry in json.loads(params["input_json"])["ids"]}
            return _response(
                {"response": {"store_items": [i for i in state["items"] if i["appid"] in wanted]}}
            )

        return _response({"items": state["search"]})

    for module in (steam_store_items, steam_game_explorer, steam_featured_games_source):
        monkeypatch.setattr(module.httpx, "get", fake_get)

    return state


def explorer():
    items = SteamStoreItems(policy=POLICY, sleep=lambda _: None)
    return SteamGameExplorer(items, policy=POLICY, sleep=lambda _: None)


def searched(steam):
    return [params for url, params in steam["calls"] if "search/results" in url]


# --- Fichas de Steam -----------------------------------------------------------


def test_store_items_build_full_image_urls_and_the_game_card(steam):
    steam["items"] = [store_item(3513350, "Wuthering Waves")]

    game = SteamStoreItems(policy=POLICY, sleep=lambda _: None).details(["3513350"])["3513350"]

    # La ruta lleva la carpeta con código: sin ella, Steam responde 404.
    assert game.image == (
        "https://shared.akamai.steamstatic.com/store_item_assets/"
        "steam/apps/3513350/c0de/library_capsule.jpg?t=9"
    )
    assert game.hero.endswith("/beef/library_hero.jpg?t=9")
    assert game.capsule.endswith("/cafe/capsule_616x353.jpg?t=9")
    assert game.description == "Un juego de prueba."
    # Por peso, y sin las etiquetas cuyo nombre no se conoce.
    assert game.tags == ("Rol", "Acción")
    assert game.developers == ("Estudio A", "Estudio B")
    assert game.release_date == date(2025, 4, 28)
    assert (game.review, game.review_percent) == ("Muy positivas", 91)
    assert (game.price, game.original_price, game.discount) == (16990.0, 169900.0, 90)


def test_store_items_are_kept_an_hour_and_unknown_games_are_left_out(steam):
    steam["items"] = [store_item(10, "Uno")]
    items = SteamStoreItems(policy=POLICY, sleep=lambda _: None)

    assert set(items.details(["10", "20"])) == {"10"}
    items.details(["10"])

    item_calls = [url for url, _ in steam["calls"] if "GetItems" in url]
    assert len(item_calls) == 1


def test_a_free_game_or_one_without_a_discount_has_no_original_price(steam):
    steam["items"] = [
        store_item(1, "Gratis", best_purchase_option=None, is_free=True),
        store_item(2, "Normal", best_purchase_option={"final_price_in_cents": "5000000"}),
    ]

    found = SteamStoreItems(policy=POLICY, sleep=lambda _: None).details(["1", "2"])

    assert (found["1"].price, found["1"].is_free) == (None, True)
    assert (found["2"].price, found["2"].original_price, found["2"].discount) == (50000.0, None, 0)


def test_without_the_tag_list_the_cards_come_without_tags(steam):
    steam["items"] = [store_item(1, "Uno")]
    steam["fail"] = {"GetTagList"}

    game = SteamStoreItems(policy=POLICY, sleep=lambda _: None).details(["1"])["1"]

    assert game.tags == ()
    assert game.name == "Uno"


# --- Explorar ------------------------------------------------------------------


def test_explore_sends_the_genre_tags_order_and_price_to_steam(steam):
    steam["search"] = [{"name": "Uno", "logo": logo(1)}]
    steam["items"] = [store_item(1, "Uno")]

    page = explorer().explore(
        ExploreQuery(genre="rol", tags=("mundo-abierto",), sort="precio-asc", price="ofertas", page=2)
    )

    params = searched(steam)[0]
    assert params["tags"] == "122,1695"
    assert params["filter"] == "topsellers"
    assert params["sort_by"] == "Price_ASC"
    assert params["specials"] == 1
    assert params["page"] == 2
    assert params["cc"] == "co"
    assert [game.name for game in page.items] == ["Uno"]
    assert page.has_more is False


def test_a_full_page_says_there_are_more(steam):
    steam["search"] = [{"name": f"J{n}", "logo": logo(n)} for n in range(1, 26)]

    page = explorer().explore(ExploreQuery())

    assert len(page.items) == 25
    assert page.has_more is True
    assert "tags" not in searched(steam)[0]


def test_without_the_cards_the_list_still_comes_with_built_images(steam):
    steam["search"] = [{"name": "Uno", "logo": logo(1)}, "raro", {"name": "", "logo": logo(2)}]
    steam["fail"] = {"GetItems"}

    page = explorer().explore(ExploreQuery(genre="accion"))

    assert [(game.id, game.name) for game in page.items] == [("1", "Uno")]
    assert page.items[0].image.endswith("/1/library_600x900.jpg")


def test_the_same_page_is_reused(steam):
    steam["search"] = [{"name": "Uno", "logo": logo(1)}]
    pages = explorer()

    pages.explore(ExploreQuery(genre="rol"))
    pages.explore(ExploreQuery(genre="rol"))

    assert len(searched(steam)) == 1


@pytest.mark.parametrize(
    "query",
    [
        ExploreQuery(genre="musica"),
        ExploreQuery(tags=("otra",)),
        ExploreQuery(sort="nombre"),
        ExploreQuery(price="caro"),
        ExploreQuery(page=0),
        ExploreQuery(page=21),
    ],
)
def test_use_case_rejects_unknown_filters(query):
    class Never:
        def explore(self, query):
            raise AssertionError("no debía consultar")

    with pytest.raises(ValueError):
        ExploreGames(Never()).execute(query)


def test_use_case_drops_repeated_tags():
    seen = []

    class Record:
        def explore(self, query):
            seen.append(query)
            return ExplorePage()

    ExploreGames(Record()).execute(ExploreQuery(tags=("indie", "indie", "anime")))

    assert seen[0].tags == ("indie", "anime")


def test_explore_endpoint(monkeypatch):
    class Fixed:
        def explore(self, query):
            return ExplorePage(
                items=[
                    ExploreGame(
                        id="1",
                        name=f"Juego {query.genre} {query.page}",
                        tags=("Rol",),
                        release_date=date(2025, 4, 28),
                        price=1000.0,
                    )
                ],
                has_more=True,
            )

    monkeypatch.setattr(main.explore_games, "explorer", Fixed())

    data = client.get("/games/explore?genre=rol&page=3&tag=indie&tag=anime").json()

    assert data["genre"] == "rol"
    assert data["page"] == 3
    assert data["has_more"] is True
    assert data["items"][0]["name"] == "Juego rol 3"
    assert data["items"][0]["release_date"] == "2025-04-28"
    assert data["items"][0]["tags"] == ["Rol"]

    assert client.get("/games/explore?genre=musica").status_code == 422
    assert client.get("/games/explore?page=21").status_code == 422
    assert client.get("/games/explore?sort=nombre").status_code == 422


def test_explore_endpoint_answers_503_when_steam_fails(monkeypatch):
    from app.infrastructure.external.resilient_http import ExternalSourceError

    class Broken:
        def explore(self, query):
            raise ExternalSourceError("Steam", "timeout")

    monkeypatch.setattr(main.explore_games, "explorer", Broken())

    answer = client.get("/games/explore")

    assert answer.status_code == 503
    assert answer.json()["detail"] == {"source": "Steam", "reason": "source_unavailable"}


# --- Portada: imágenes reales ----------------------------------------------------


def test_featured_games_use_the_real_image_paths(steam):
    steam["search"] = [{"name": "Wuthering Waves", "logo": logo(3513350)}, {"name": "Viejo", "logo": logo(5)}]
    steam["items"] = [store_item(3513350, "Wuthering Waves")]

    source = SteamFeaturedGamesSource(
        policy=POLICY,
        sleep=lambda _: None,
        store_items=SteamStoreItems(policy=POLICY, sleep=lambda _: None),
    )

    games = source.list(None)

    assert games[0].image.endswith("/3513350/c0de/library_capsule.jpg?t=9")
    assert games[0].header.endswith("/3513350/f00d/header.jpg?t=9")
    # Un juego sin ficha conserva la ruta armada.
    assert games[1].image.endswith("/5/library_600x900.jpg")


def test_featured_games_keep_built_images_when_the_cards_fail(steam):
    steam["search"] = [{"name": "Uno", "logo": logo(1)}]
    steam["fail"] = {"GetItems"}

    source = SteamFeaturedGamesSource(
        policy=POLICY,
        sleep=lambda _: None,
        store_items=SteamStoreItems(policy=POLICY, sleep=lambda _: None),
    )

    assert source.list(None)[0].image.endswith("/1/library_600x900.jpg")
