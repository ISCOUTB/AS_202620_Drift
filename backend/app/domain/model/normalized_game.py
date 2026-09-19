from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class NormalizedGame:
    id: str
    name: str
    source: str
    platform: str
    price: float
    currency: str
    discount: int
    captured_at: datetime
