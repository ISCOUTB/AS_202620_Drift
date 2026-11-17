from typing import Iterable, List, Optional

from app.domain.services.platforms import platform_of_store, platforms_of_stores


class Game:
    def __init__(
        self,
        id: str,
        name: str,
        prices: dict,
        unavailable_sources: Optional[list[str]] = None,
        image: Optional[str] = None,
        links: Optional[dict] = None,
        cached_sources: Optional[dict] = None,
        discounts: Optional[dict] = None,
    ):
        self.id = str(id)
        self.name = name
        self.prices = prices
        self.unavailable_sources = unavailable_sources or []
        self.image = image
        # Página de compra en cada tienda, con las mismas claves que `prices`.
        self.links = links or {}
        # Fuentes cuya respuesta salió de la copia de respaldo porque la
        # fuente no respondió: nombre de la fuente -> fecha ISO 8601 (UTC)
        # en que se obtuvo ese dato (ADR-0015).
        self.cached_sources = cached_sources or {}
        # Porcentaje de descuento que la tienda anuncia sobre su precio
        # normal, con las mismas claves que `prices`. Solo las tiendas con
        # una oferta activa aparecen aquí.
        self.discounts = discounts or {}

    @property
    def platforms(self) -> List[str]:
        """Plataformas para las que hay al menos un precio."""

        return platforms_of_stores(self.prices)

    def restricted_to(self, platforms: Iterable[str]) -> "Game":
        """
        El mismo juego solo con las tiendas de las plataformas pedidas.

        Quien solo tiene una consola no necesita ver precios de PC. Si no
        queda ninguna tienda, `prices` queda vacío y quien llama decide si
        muestra el juego.
        """

        wanted = set(platforms)

        def keep(by_store: dict) -> dict:
            return {
                store: value
                for store, value in by_store.items()
                if platform_of_store(store) in wanted
            }

        return Game(
            id=self.id,
            name=self.name,
            prices=keep(self.prices),
            unavailable_sources=list(self.unavailable_sources),
            image=self.image,
            links=keep(self.links),
            cached_sources=dict(self.cached_sources),
            discounts=keep(self.discounts),
        )
