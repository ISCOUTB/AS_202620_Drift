"""Upstream simulado para el experimento E6 (degradación bajo carga).

Reemplaza a Steam, CheapShark, PlayStation Store, la tienda de Xbox y la tasa
de cambio con latencias fijas, para que la medición no dependa de servicios
reales. Xbox se añadió el 13 de noviembre de 2026, cuando la búsqueda empezó a
consultarla: sin ella, cada búsqueda la contaría como fuente caída.

CheapShark es la fuente degradada: las consultas marcadas como lentas tardan
más de 5 s. Qué consultas son lentas depende solo del número de la consulta,
así que el conjunto es idéntico en todas las corridas (18 de 50, 36 %).

Uso (desde la raíz del repositorio):
    python scripts/stub_upstream.py            # escucha en 127.0.0.1:9100
    STUB_SIN_DEGRADACION=1 python scripts/stub_upstream.py   # sin fuente lenta (S14)
"""

import asyncio
import os
import re
import zlib

import uvicorn
from fastapi import FastAPI

STEAM_DELAY_SECONDS = 0.15
CHEAPSHARK_DELAY_SECONDS = 0.25
CHEAPSHARK_SLOW_DELAY_SECONDS = 6.0
PLAYSTATION_DELAY_SECONDS = 0.25
EXCHANGE_DELAY_SECONDS = 0.10
XBOX_SEARCH_DELAY_SECONDS = 0.20
XBOX_CATALOG_DELAY_SECONDS = 0.25

# Identificador de Xbox -> nombre del juego (lo llenan los buscadores).
XBOX_NAMES: dict[str, str] = {}

# Residuos (número de consulta módulo 20) que CheapShark responde lento.
SLOW_RESIDUES = {1, 4, 7, 10, 13, 16, 19}

# S14 mide E1 en operación normal: con STUB_SIN_DEGRADACION=1 ninguna consulta
# es lenta. Sin la variable, el comportamiento de E6 no cambia.
if os.getenv("STUB_SIN_DEGRADACION") == "1":
    SLOW_RESIDUES = set()

GAMES_PER_QUERY = 3

app = FastAPI(title="Upstream simulado E6")


def query_number(query: str) -> int:
    # El número de la consulta es el último del texto ("e6 juego 07" -> 7).
    numbers = re.findall(r"\d+", query)
    return int(numbers[-1]) if numbers else 0


def is_slow(query: str) -> bool:
    return query_number(query) % 20 in SLOW_RESIDUES


def app_ids(query: str) -> list[int]:
    base = 100000 + (zlib.crc32(query.strip().lower().encode()) % 800000)
    return [base + offset for offset in range(GAMES_PER_QUERY)]


def game_name(query: str, index: int) -> str:
    return f"{query.strip()} edicion {index + 1}"


@app.get("/steam/api/storesearch/")
async def steam_search(term: str):
    await asyncio.sleep(STEAM_DELAY_SECONDS)

    return {
        "items": [
            {"id": app_id, "name": game_name(term, index)}
            for index, app_id in enumerate(app_ids(term))
        ]
    }


@app.get("/steam/api/appdetails")
async def steam_details(appids: int):
    await asyncio.sleep(STEAM_DELAY_SECONDS)

    return {
        str(appids): {
            "success": True,
            "data": {
                "price_overview": {"final": 9990000 + (appids % 1000) * 100},
                "header_image": f"https://stub.invalid/{appids}/header.jpg",
            },
        }
    }


@app.get("/cheapshark/api/1.0/deals")
async def cheapshark_deals(title: str):
    await asyncio.sleep(
        CHEAPSHARK_SLOW_DELAY_SECONDS if is_slow(title) else CHEAPSHARK_DELAY_SECONDS
    )

    deals = []

    for index, app_id in enumerate(app_ids(title)):
        for store_id, price in (("7", "19.99"), ("25", "21.49")):
            deals.append({
                "title": game_name(title, index),
                "storeID": store_id,
                "gameID": str(app_id),
                "steamAppID": str(app_id),
                "salePrice": price,
                "thumb": f"https://stub.invalid/{app_id}/thumb.jpg",
            })

    return deals


@app.get("/cheapshark/api/1.0/stores")
async def cheapshark_stores():
    await asyncio.sleep(EXCHANGE_DELAY_SECONDS)

    return [
        {"storeID": "1", "storeName": "Steam", "isActive": 1},
        {"storeID": "7", "storeName": "GOG", "isActive": 1},
        {"storeID": "25", "storeName": "Epic Games Store", "isActive": 1},
    ]


@app.get("/playstation/store/api/chihiro/00_09_000/tumbler/co/es/999/{query}")
async def playstation_search(query: str):
    await asyncio.sleep(PLAYSTATION_DELAY_SECONDS)

    name = query.replace("_", " ")

    return {
        "links": [
            {
                "id": f"STUB-{zlib.crc32(name.encode())}-{index}",
                "name": game_name(name, index),
                "playable_platform": ["PS5"],
                "default_sku": {
                    "price": 2499,
                    "display_price": "US$24.99",
                },
            }
            for index in range(GAMES_PER_QUERY)
        ]
    }


def xbox_ids(query: str) -> list[str]:
    """Identificadores de Xbox de la consulta; recuerda el nombre de cada uno.

    Los buscadores de Xbox entregan identificadores y el catálogo, que solo
    recibe esos identificadores, tiene que saber a qué juego corresponden.
    """

    base = zlib.crc32(query.strip().lower().encode())
    ids = [f"9STUB{base:010d}{index}" for index in range(GAMES_PER_QUERY)]

    for index, product_id in enumerate(ids):
        XBOX_NAMES[product_id] = game_name(query, index)

    return ids


# Xbox (desde S14, tras añadir la tienda de Xbox a la búsqueda): los dos
# buscadores de la tienda y el catálogo de precios, sin degradación.
@app.get("/xbox-suggest/msstoreapiprod/api/autosuggest")
async def xbox_suggest(query: str):
    await asyncio.sleep(XBOX_SEARCH_DELAY_SECONDS)

    return {
        "ResultSets": [
            {
                "Suggests": [
                    {
                        "Metas": [
                            {"Key": "BigCatalogId", "Value": product_id},
                            {"Key": "ProductType", "Value": "Games"},
                        ]
                    }
                    for product_id in xbox_ids(query)
                ]
            }
        ]
    }


@app.get("/xbox-search/v9.0/search")
async def xbox_search(query: str):
    await asyncio.sleep(XBOX_SEARCH_DELAY_SECONDS)

    return {
        "Payload": {
            "SearchResults": [
                {"ProductId": product_id, "Title": game_name(query, index)}
                for index, product_id in enumerate(xbox_ids(query))
            ]
        }
    }


@app.get("/xbox-catalog/v7.0/products")
async def xbox_catalog(bigIds: str):
    await asyncio.sleep(XBOX_CATALOG_DELAY_SECONDS)

    names = XBOX_NAMES

    return {
        "Products": [
            {
                "ProductId": product_id,
                "ProductKind": "Game",
                "LocalizedProperties": [
                    {"ProductTitle": names.get(product_id, product_id), "Images": []}
                ],
                "DisplaySkuAvailabilities": [
                    {
                        "Availabilities": [
                            {
                                "Actions": ["Purchase"],
                                "OrderManagementData": {
                                    "Price": {
                                        "ListPrice": 99900,
                                        "MSRP": 99900,
                                        "CurrencyCode": "COP",
                                    }
                                },
                            }
                        ]
                    }
                ],
            }
            for product_id in bigIds.split(",")
        ]
    }


@app.get("/exchange/v6/latest/USD")
async def exchange_rate():
    await asyncio.sleep(EXCHANGE_DELAY_SECONDS)

    return {"result": "success", "rates": {"COP": 4000}}


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=int(os.getenv("E6_STUB_PORT", "9100")),
        log_level="warning",
    )
