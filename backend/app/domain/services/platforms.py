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


# Tiendas consultadas directamente para Colombia. Las demás tiendas de PC
# llegan por IsThereAnyDeal o CheapShark con su precio de Estados Unidos, y
# algunas no venden el juego en Colombia (ADR-0024).
_COLOMBIA_PRICE_STORES = {"Steam", "PlayStation", "Xbox", "Microsoft Store"}


def platform_of_store(store: str) -> str:
    return _CONSOLE_STORES.get(store, PC)


def has_colombia_price(store: str) -> bool:
    return store in _COLOMBIA_PRICE_STORES


def purchase_order(store: str, price: float) -> tuple:
    """Clave para ordenar: primero los precios de Colombia, luego por precio."""

    return (not has_colombia_price(store), price, store)


def platforms_of_stores(stores: Iterable[str]) -> List[str]:
    """Plataformas de un conjunto de tiendas, siempre en el mismo orden."""

    found = {platform_of_store(store) for store in stores}

    return [platform for platform in ALL_PLATFORMS if platform in found]
