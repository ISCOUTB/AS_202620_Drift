from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class NormalizedGame:
    id: str
    name: str
    source: str
    platform: str
    price: Optional[float]
    currency: str
    discount: int
    captured_at: datetime
