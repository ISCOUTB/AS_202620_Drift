from typing import Optional


class Game:
    def __init__(
        self,
        id: int,
        name: str,
        prices: dict,
        unavailable_sources: Optional[list[str]] = None,
    ):
        self.id = id
        self.name = name
        self.prices = prices
        self.unavailable_sources = unavailable_sources or []