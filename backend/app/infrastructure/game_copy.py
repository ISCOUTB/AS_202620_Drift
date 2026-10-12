from typing import List

from app.domain.model.game import Game


def copy_games(games: List[Game]) -> List[Game]:
    """
    Copias independientes de los juegos guardados en caché o en memoria.

    Los repositorios que combinan tiendas modifican `prices` y
    `unavailable_sources`; sin copias, una búsqueda alteraría lo que
    reciben las demás.
    """

    return [
        Game(
            id=game.id,
            name=game.name,
            prices=dict(game.prices),
            unavailable_sources=list(game.unavailable_sources),
            image=game.image,
        )
        for game in games
    ]
