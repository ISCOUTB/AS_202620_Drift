import httpx

from typing import List
from app.domain.model.game import Game
from app.domain.ports.game_repository import GameRepository


class SteamGameRepository(GameRepository):

    def search(self, query: str) -> List[Game]:
        response = httpx.get(
            "https://store.steampowered.com/api/storesearch/",
            params={
                "term": query,
                "cc": "co",
                "l": "spanish"
            }
        )

        response.raise_for_status()

        data = response.json()

        games = []

        for item in data.get("items", []):
            app_id = item["id"]

            details_response = httpx.get(
                "https://store.steampowered.com/api/appdetails",
                params={
                    "appids": app_id,
                    "cc": "co",
                    "l": "spanish"
                }
            )

            details_response.raise_for_status()

            details_data = details_response.json()
            game_data = details_data.get(str(app_id), {}).get("data", {})

            prices = {}

            price_overview = game_data.get("price_overview")

            if price_overview:
                prices["Steam"] = price_overview.get("final", 0) / 100

            games.append(
                Game(
                    id=app_id,
                    name=item["name"],
                    prices=prices
                )
            )

        return games