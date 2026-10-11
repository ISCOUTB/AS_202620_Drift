import asyncio
import os
import re
import time
import unicodedata

import httpx
from fastapi import FastAPI, Query

app = FastAPI(
    title="DRIFT Serverless API",
    version="1.0.0",
)


STEAM_SEARCH_URL = "https://store.steampowered.com/api/storesearch/"
STEAM_DETAILS_URL = "https://store.steampowered.com/api/appdetails/"

CHEAPSHARK_URL = "https://www.cheapshark.com/api/1.0"
EXCHANGE_RATE_URL = "https://open.er-api.com/v6/latest/USD"

# CheapShark rechaza peticiones sin un User-Agent descriptivo.
CHEAPSHARK_HEADERS = {
    "User-Agent": "DRIFT/1.0 (proyecto academico AS_202620 UTB)",
    "Accept": "application/json",
}

# Steam ya se consulta directamente y en pesos colombianos.
CHEAPSHARK_EXCLUDED_STORE_IDS = {"1"}

FALLBACK_USD_TO_COP = float(os.getenv("USD_TO_COP_RATE", "3250"))

STORES_CACHE_SECONDS = 24 * 60 * 60
EXCHANGE_RATE_CACHE_SECONDS = 12 * 60 * 60

# Sobrevive mientras la función serverless siga "caliente".
_cache = {
    "stores": None,
    "stores_loaded_at": 0.0,
    "usd_to_cop": None,
    "usd_to_cop_loaded_at": 0.0,
}


def normalize_game_name(name: str) -> str:
    name = re.sub(r"[™®©]", " ", name)
    name = unicodedata.normalize("NFKD", name)

    name = "".join(
        character
        for character in name
        if not unicodedata.combining(character)
    )

    name = re.sub(r"[^a-z0-9]+", " ", name.casefold())

    return " ".join(name.split())


async def get_game_details(
    client: httpx.AsyncClient,
    item: dict,
) -> dict:
    app_id = item["id"]

    response = await client.get(
        STEAM_DETAILS_URL,
        params={
            "appids": app_id,
            "cc": "co",
            "l": "spanish",
        },
    )
    response.raise_for_status()

    data = response.json()
    game_data = data.get(str(app_id), {}).get("data", {})

    prices = {}

    price_overview = game_data.get("price_overview")

    if price_overview:
        prices["Steam"] = price_overview.get("final", 0) / 100

    return {
        "id": app_id,
        "name": item["name"],
        "prices": prices,
        "unavailable_sources": [],
        "image": game_data.get("header_image"),
    }


async def search_steam(
    client: httpx.AsyncClient,
    query: str,
) -> list[dict]:
    response = await client.get(
        STEAM_SEARCH_URL,
        params={
            "term": query,
            "cc": "co",
            "l": "spanish",
        },
    )
    response.raise_for_status()

    data = response.json()
    items = data.get("items", [])[:5]

    if not items:
        return []

    return list(
        await asyncio.gather(
            *[
                get_game_details(client, item)
                for item in items
            ]
        )
    )


async def get_usd_to_cop(client: httpx.AsyncClient) -> float:
    """CheapShark entrega precios en USD; Steam los entrega en COP."""

    if (
        _cache["usd_to_cop"]
        and time.monotonic() - _cache["usd_to_cop_loaded_at"]
        < EXCHANGE_RATE_CACHE_SECONDS
    ):
        return _cache["usd_to_cop"]

    try:
        response = await client.get(EXCHANGE_RATE_URL)
        response.raise_for_status()

        rate = float(response.json()["rates"]["COP"])
    except (httpx.HTTPError, AttributeError, KeyError, TypeError, ValueError):
        # Sin tasa actualizada se usa la última conocida o la configurada.
        return _cache["usd_to_cop"] or FALLBACK_USD_TO_COP

    _cache["usd_to_cop"] = rate
    _cache["usd_to_cop_loaded_at"] = time.monotonic()

    return rate


async def get_cheapshark_stores(client: httpx.AsyncClient) -> dict:
    if (
        _cache["stores"]
        and time.monotonic() - _cache["stores_loaded_at"]
        < STORES_CACHE_SECONDS
    ):
        return _cache["stores"]

    response = await client.get(
        f"{CHEAPSHARK_URL}/stores",
        headers=CHEAPSHARK_HEADERS,
    )
    response.raise_for_status()

    stores = response.json()

    if not isinstance(stores, list):
        return {}

    _cache["stores"] = {
        str(store["storeID"]): store["storeName"]
        for store in stores
        if store.get("isActive")
    }
    _cache["stores_loaded_at"] = time.monotonic()

    return _cache["stores"]


async def search_cheapshark(
    client: httpx.AsyncClient,
    query: str,
) -> list[dict]:
    """Precios de tiendas de PC, convertidos a COP."""

    try:
        response, stores, usd_to_cop = await asyncio.gather(
            client.get(
                f"{CHEAPSHARK_URL}/deals",
                params={
                    "title": query,
                    "pageSize": 60,
                },
                headers=CHEAPSHARK_HEADERS,
            ),
            get_cheapshark_stores(client),
            get_usd_to_cop(client),
        )
        response.raise_for_status()
    except httpx.HTTPError:
        # CheapShark es secundaria: la búsqueda sigue con Steam.
        return []

    deals = response.json()

    if not isinstance(deals, list):
        return []

    games_by_key = {}

    for deal in deals:
        store_id = str(deal.get("storeID"))

        if store_id in CHEAPSHARK_EXCLUDED_STORE_IDS:
            continue

        store_name = stores.get(store_id)

        if not store_name or not deal.get("title"):
            continue

        try:
            price = round(float(deal["salePrice"]) * usd_to_cop, 2)
        except (KeyError, TypeError, ValueError):
            continue

        steam_app_id = deal.get("steamAppID")
        key = steam_app_id or f"cheapshark-{deal.get('gameID')}"

        game = games_by_key.setdefault(
            key,
            {
                "steam_app_id": steam_app_id,
                "name": deal["title"],
                "prices": {},
                "image": deal.get("thumb"),
            },
        )

        current_price = game["prices"].get(store_name)

        if current_price is None or price < current_price:
            game["prices"][store_name] = price

    return list(games_by_key.values())


def merge_games(
    steam_games: list[dict],
    cheapshark_games: list[dict],
) -> list[dict]:
    games_by_id = {
        str(game["id"]): game
        for game in steam_games
    }

    games_by_name = {
        normalize_game_name(game["name"]): game
        for game in steam_games
    }

    for game in cheapshark_games:
        # El steamAppID une el juego con el resultado de Steam;
        # si no existe, se compara por nombre.
        existing_game = (
            games_by_id.get(str(game["steam_app_id"]))
            or games_by_name.get(normalize_game_name(game["name"]))
        )

        if existing_game:
            for store, price in game["prices"].items():
                existing_game["prices"].setdefault(store, price)

            existing_game["image"] = existing_game["image"] or game["image"]
            continue

        if not game["steam_app_id"]:
            continue

        new_game = {
            "id": int(game["steam_app_id"]),
            "name": game["name"],
            "prices": game["prices"],
            "unavailable_sources": [],
            "image": game["image"],
        }

        steam_games.append(new_game)
        games_by_id[str(new_game["id"])] = new_game
        games_by_name[normalize_game_name(new_game["name"])] = new_game

    return steam_games


@app.get("/api")
async def root():
    return {
        "status": "ok",
        "service": "DRIFT Serverless API",
        "message": "API funcionando correctamente",
    }


@app.get("/api/games/search")
async def search_games(
    q: str = Query(..., min_length=1),
):
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Las tiendas se consultan en paralelo.
        steam_games, cheapshark_games = await asyncio.gather(
            search_steam(client, q),
            search_cheapshark(client, q),
        )

        return merge_games(steam_games, cheapshark_games)
