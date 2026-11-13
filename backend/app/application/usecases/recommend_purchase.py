import logging
from typing import Dict, Iterable, Optional

from app.application.usecases.estimate_compatibility import (
    UNKNOWN,
    EstimateCompatibility,
)
from app.domain.model.account import PC, Device
from app.domain.services.recommendation import (
    CONSOLE,
    INSUFFICIENT,
    MINIMUM,
    RECOMMENDED,
    UNVERIFIED,
    DeviceVerdict,
    Recommendation,
    recommend,
)

logger = logging.getLogger("drift")

_EXPERIENCE_OF_STATUS = {
    "Compatible": RECOMMENDED,
    "Compatible con limitaciones": MINIMUM,
    "No compatible": INSUFFICIENT,
}


class RecommendPurchase:
    """
    Dónde comprar un juego y en cuál de sus dispositivos jugarlo.

    Combina los precios que el usuario ya tiene en pantalla con la
    compatibilidad de cada uno de sus PC. Las consolas no se comprueban: lo
    que vende su tienda corre en ellas.
    """

    def __init__(self, estimate_compatibility: EstimateCompatibility):
        self.estimate_compatibility = estimate_compatibility

    def execute(
        self,
        game_id: str,
        prices: Dict[str, float],
        discounts: Optional[Dict[str, int]] = None,
        devices: Iterable[Device] = (),
    ) -> Recommendation:
        verdicts = [
            DeviceVerdict(
                device_id=device.id,
                name=device.name,
                kind=device.kind,
                experience=(
                    self._pc_experience(game_id, device)
                    if device.kind == PC
                    else CONSOLE
                ),
            )
            for device in devices
        ]

        return recommend(prices, discounts, verdicts)

    def _pc_experience(self, game_id: str, device: Device) -> str:
        # Los requisitos de PC salen de Steam: sin su identificador
        # (numérico) no hay con qué comparar.
        if not str(game_id).isdecimal():
            return UNVERIFIED

        specs = device.specs

        try:
            result = self.estimate_compatibility.execute(
                game_id=int(game_id),
                ram_gb=specs.ram_gb,
                gpu_score=specs.gpu_score,
                storage_gb=specs.storage_gb,
                gpu_name=specs.gpu_name,
                cpu_name=specs.cpu_name,
                cpu_score=specs.cpu_score,
            )
        except Exception:
            # Si la fuente de requisitos falla, la recomendación sigue con
            # el precio y avisa que ese PC quedó sin comprobar.
            logger.warning("No se pudo comprobar la compatibilidad de un PC")

            return UNVERIFIED

        compared = [
            check
            for check in result.get("checks", [])
            if check["level"] != UNKNOWN
        ]

        if not compared:
            return UNVERIFIED

        return _EXPERIENCE_OF_STATUS.get(result["status"], UNVERIFIED)
