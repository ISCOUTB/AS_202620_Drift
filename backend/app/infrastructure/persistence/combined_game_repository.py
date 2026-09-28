import httpx
import re
import unicodedata
from typing import List

from app.domain.model.game import Game
from app.domain.ports.game_repository import GameRepository


def normalize_game_name(name: str) -> str:
    name = unicodedata.normalize("NFKD", name)

    name = "".join(
        character
        for character in name
        if not unicodedata.combining(character)
    )

    name = name.casefold()

    # Eliminar símbolos como ™, ® y ©
    name = re.sub(r"[™®©]", "", name)

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
        games = self.primary_repository.search(query)

        games_by_name = {
            normalize_game_name(game.name): game
            for game in games
        }

        try:
            secondary_games = self.secondary_repository.search(query)
        except httpx.HTTPError:
            # PlayStation es secundaria: conserva Steam o el catálogo local.
            secondary_games = []

        for game in secondary_games:
            normalized_name = normalize_game_name(game.name)

            existing_game = games_by_name.get(normalized_name)

            if existing_game:
                existing_game.prices.update(game.prices)
                continue

            games.append(game)
            games_by_name[normalized_name] = game

        return games