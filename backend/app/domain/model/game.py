from typing import Optional


class Game:
    def __init__(
        self,
        id: str,
        name: str,
        prices: dict,
        unavailable_sources: Optional[list[str]] = None,
        image: Optional[str] = None,
        links: Optional[dict] = None,
    ):
        self.id = str(id)
        self.name = name
        self.prices = prices
        self.unavailable_sources = unavailable_sources or []
        self.image = image
        # Página de compra en cada tienda, con las mismas claves que `prices`.
        self.links = links or {}
