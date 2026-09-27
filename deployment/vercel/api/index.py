import asyncio

import httpx
from fastapi import FastAPI, Query

app = FastAPI(
    title="DRIFT Serverless API",
    version="1.0.0",
)


STEAM_SEARCH_URL = "https://store.steampowered.com/api/storesearch/"
STEAM_DETAILS_URL = "https://store.steampowered.com/api/appdetails/"


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
    }

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
        response = await client.get(
            STEAM_SEARCH_URL,
            params={
                "term": q,
                "cc": "co",
                "l": "spanish",
            },
        )
        response.raise_for_status()

        data = response.json()
        items = data.get("items", [])[:5]

        if not items:
            return []

        games = await asyncio.gather(
            *[
                get_game_details(client, item)
                for item in items
            ]
        )

        return games