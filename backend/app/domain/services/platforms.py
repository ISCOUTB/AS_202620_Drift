"""
Plataformas en las que se juega lo que vende cada tienda.

La ficha del problema pide filtrar según las plataformas que tiene el
usuario. Un precio pertenece a una tienda, y cada tienda vende para una
plataforma: PlayStation Store para PlayStation, la tienda de Xbox para
Xbox y todas las demás (Steam, GOG, Epic, Microsoft Store…) para PC.
"""

from typing import Iterable, List

PC = "PC"
PLAYSTATION = "PlayStation"
XBOX = "Xbox"

ALL_PLATFORMS = (PC, PLAYSTATION, XBOX)

_CONSOLE_STORES = {
    "PlayStation": PLAYSTATION,
    "Xbox": XBOX,
}


def platform_of_store(store: str) -> str:
    return _CONSOLE_STORES.get(store, PC)


def platforms_of_stores(stores: Iterable[str]) -> List[str]:
    """Plataformas de un conjunto de tiendas, siempre en el mismo orden."""

    found = {platform_of_store(store) for store in stores}

    return [platform for platform in ALL_PLATFORMS if platform in found]
