from app.domain.ports.game_requirements_repository import (
    GameRequirementsRepository,
)


class EstimateCompatibility:
    def __init__(self, requirements_repository: GameRequirementsRepository):
        self.requirements_repository = requirements_repository

    def execute(self, game_id: int, ram_gb: int, gpu_score: int) -> dict:
        requirements = self.requirements_repository.get_by_game_id(game_id)

        if requirements is None:
            return {
                "game_id": game_id,
                "status": "Requisitos no disponibles",
            }

        if (
            ram_gb < requirements.minimum_ram_gb
            or gpu_score < requirements.minimum_gpu_score
        ):
            status = "No compatible"
        elif (
            ram_gb >= requirements.recommended_ram_gb
            and gpu_score >= requirements.recommended_gpu_score
        ):
            status = "Compatible"
        else:
            status = "Compatible con limitaciones"

        return {
            "game_id": game_id,
            "status": status,
            "minimum_ram_gb": requirements.minimum_ram_gb,
            "recommended_ram_gb": requirements.recommended_ram_gb,
            "minimum_gpu_score": requirements.minimum_gpu_score,
            "recommended_gpu_score": requirements.recommended_gpu_score,
        }