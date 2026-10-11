import httpx
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from typing import List

from app.domain.model.game import Game
from app.domain.ports.game_repository import GameRepository


def normalize_game_name(name: str) -> str:
    # Eliminar símbolos como ™, ® y © antes de NFKD,
    # que convertiría "™" en las letras "TM".
    name = re.sub(r"[™®©]", " ", name)

    name = unicodedata.normalize("NFKD", name)

    name = "".join(
        character
        for character in name
        if not unicodedata.combining(character)
    )

    name = name.casefold()

    # Eliminar información adicional típica de PlayStation
    name = re.sub(
        r"\b(edicion|edition)\s+(estandar|standard|ultimate|deluxe|digital)\b.*$",
        "",
        name,
    )

    name = re.sub(
        r"\bpara\s+ps[45]\s*(y\s*ps[45])?.*$",
        "",
        name,
    )

    # Eliminar "PS4", "PS5", etc. al final
    name = re.sub(
        r"\bps[45](\s+y\s+ps[45])?.*$",
        "",
        name,
    )

    # Normalizar caracteres restantes
    name = re.sub(r"[^a-z0-9]+", " ", name)

    return " ".join(name.split())


class CombinedGameRepository(GameRepository):
    """Combina resultados de diferentes tiendas."""

    def __init__(
        self,
        primary_repository: GameRepository,
        secondary_repository: GameRepository,
    ):
        self.primary_repository = primary_repository
        self.secondary_repository = secondary_repository

    def search(self, query: str) -> List[Game]:
        # Las tiendas se consultan en paralelo, no una después de otra.
        with ThreadPoolExecutor(max_workers=1) as executor:
            secondary_search = executor.submit(
                self.secondary_repository.search,
                query,
            )

            games = self.primary_repository.search(query)

            try:
                secondary_games = secondary_search.result()
            except httpx.HTTPError:
                # La tienda secundaria es opcional: conserva lo ya encontrado.
                secondary_games = []

        games_by_name = {
            normalize_game_name(game.name): game
            for game in games
        }

        games_by_id = {
            game.id: game
            for game in games
        }

        for game in secondary_games:
            normalized_name = normalize_game_name(game.name)

            # El id coincide cuando la tienda secundaria conoce el
            # identificador de Steam; si no, se compara por nombre.
            existing_game = (
                games_by_id.get(game.id)
                or games_by_name.get(normalized_name)
            )

            if existing_game:
                self._merge_prices(existing_game, game)
                existing_game.image = existing_game.image or game.image
                continue

            games.append(game)
            games_by_name[normalized_name] = game
            games_by_id[game.id] = game

        return games

    @staticmethod
    def _merge_prices(existing_game: Game, game: Game) -> None:
        """
        Una tienda puede repetir el juego (ediciones, versiones o
        entradas gratuitas de prueba): se conserva el menor precio
        real y el cero solo si no existe otro.
        """

        for store, price in game.prices.items():
            current_price = existing_game.prices.get(store)

            if (
                current_price is None
                or current_price <= 0 < price
                or 0 < price < current_price
            ):
                existing_game.prices[store] = price