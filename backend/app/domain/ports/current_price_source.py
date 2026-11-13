from abc import ABC, abstractmethod
from typing import Dict, Iterable

from app.domain.services.price_alerts import CurrentPrice


class CurrentPriceSource(ABC):
    """Precio de hoy de varios juegos a la vez, por su identificador."""

    @abstractmethod
    def best_prices(self, game_ids: Iterable[str]) -> Dict[str, CurrentPrice]:
        """
        El mejor precio de hoy de cada juego que se pudo consultar.

        Un juego que falta en la respuesta no se pudo consultar: su fuente
        no respondió o no se sabe dónde buscarlo. Nunca lanza por una fuente
        caída: las alertas son un extra y no deben romper la página.
        """
