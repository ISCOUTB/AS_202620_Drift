import httpx
import logging
import os
import re
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as SourceTimeoutError
from typing import List, Optional

from app.domain.model.game import Game
from app.domain.ports.game_repository import GameRepository
from app.infrastructure.observability import log_event


logger = logging.getLogger("drift")

DEFAULT_SOURCE_TIMEOUT_SECONDS = 3.0


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
    """
    Combina resultados de diferentes tiendas.

    La fuente secundaria es opcional: si falla o no responde dentro del
    plazo, la búsqueda continúa con lo ya encontrado y el nombre de la
    fuente queda en `unavailable_sources` de cada resultado.
    """

    def __init__(
        self,
        primary_repository: GameRepository,
        secondary_repository: GameRepository,
        secondary_name: str,
        timeout_seconds: Optional[float] = None,
    ):
        self.primary_repository = primary_repository
        self.secondary_repository = secondary_repository
        self.secondary_name = secondary_name

        if timeout_seconds is None:
            timeout_seconds = float(
                os.getenv(
                    "DRIFT_SOURCE_TIMEOUT_SECONDS",
                    DEFAULT_SOURCE_TIMEOUT_SECONDS,
                )
            )

        self.timeout_seconds = timeout_seconds

    def search(self, query: str) -> List[Game]:
        # Las tiendas se consultan en paralelo, no una después de otra.
        executor = ThreadPoolExecutor(max_workers=1)
        launched_at = time.monotonic()

        secondary_search = executor.submit(
            self.secondary_repository.search,
            query,
        )

        # No se espera al hilo al terminar: si la fuente vence, su consulta
        # acaba por el timeout HTTP del adaptador sin retener la búsqueda.
        executor.shutdown(wait=False)

        games = self.primary_repository.search(query)

        # El plazo se cuenta desde que se lanzó la consulta secundaria.
        remaining_seconds = max(
            0.0,
            self.timeout_seconds - (time.monotonic() - launched_at),
        )

        try:
            secondary_games = secondary_search.result(
                timeout=remaining_seconds,
            )
        except SourceTimeoutError:
            secondary_games = []
            self._mark_unavailable(games, "timeout", launched_at)
        except httpx.HTTPError:
            secondary_games = []
            self._mark_unavailable(games, "error", launched_at)

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

    def _mark_unavailable(
        self,
        games: List[Game],
        reason: str,
        launched_at: float,
    ) -> None:
        """Una respuesta sin una tienda no debe parecer una respuesta completa."""

        for game in games:
            if self.secondary_name not in game.unavailable_sources:
                game.unavailable_sources.append(self.secondary_name)

        log_event(
            logger,
            "source_unavailable",
            source=self.secondary_name,
            reason=reason,
            waited_ms=round((time.monotonic() - launched_at) * 1000, 2),
        )

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

                # El enlace de compra acompaña al precio que se conserva.
                if store in game.links:
                    existing_game.links[store] = game.links[store]
                else:
                    existing_game.links.pop(store, None)