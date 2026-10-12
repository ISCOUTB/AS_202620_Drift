from typing import Optional


class GameRequirements:
    """
    Requisitos de un juego para PC.

    La RAM siempre se conoce. La gráfica y el procesador (nivel de 1 a 5) y
    el almacenamiento pueden faltar cuando la fuente no los publica de forma
    reconocible. `minimum_details` y `recommended_details` conservan el
    texto original de la fuente para mostrarlo al usuario.
    """

    def __init__(
        self,
        game_id: int,
        minimum_ram_gb: int,
        recommended_ram_gb: int,
        minimum_gpu_score: Optional[int],
        recommended_gpu_score: Optional[int],
        minimum_storage_gb: Optional[int] = None,
        recommended_storage_gb: Optional[int] = None,
        minimum_details: Optional[dict] = None,
        recommended_details: Optional[dict] = None,
        source: str = "DRIFT",
        minimum_cpu_score: Optional[int] = None,
        recommended_cpu_score: Optional[int] = None,
    ):
        self.game_id = game_id
        self.minimum_ram_gb = minimum_ram_gb
        self.recommended_ram_gb = recommended_ram_gb
        self.minimum_gpu_score = minimum_gpu_score
        self.recommended_gpu_score = recommended_gpu_score
        self.minimum_storage_gb = minimum_storage_gb
        self.recommended_storage_gb = recommended_storage_gb
        self.minimum_details = minimum_details or {}
        self.recommended_details = recommended_details or {}
        self.source = source
        self.minimum_cpu_score = minimum_cpu_score
        self.recommended_cpu_score = recommended_cpu_score
