class GameRequirements:
    def __init__(
        self,
        game_id: int,
        minimum_ram_gb: int,
        recommended_ram_gb: int,
        minimum_gpu_score: int,
        recommended_gpu_score: int,
    ):
        self.game_id = game_id
        self.minimum_ram_gb = minimum_ram_gb
        self.recommended_ram_gb = recommended_ram_gb
        self.minimum_gpu_score = minimum_gpu_score
        self.recommended_gpu_score = recommended_gpu_score
