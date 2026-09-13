from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.application.usecases.estimate_compatibility import EstimateCompatibility
from app.application.usecases.search_games import SearchGames
from app.infrastructure.external.steam.steam_game_repository import (
    SteamGameRepository,
)
from app.infrastructure.persistence.in_memory_game_repository import (
    InMemoryGameRepository,
)
from app.infrastructure.persistence.in_memory_game_requirements_repository import (
    InMemoryGameRequirementsRepository,
)
from app.infrastructure.persistence.resilient_game_repository import (
    ResilientGameRepository,
)

app = FastAPI(title="DRIFT API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CompatibilityRequest(BaseModel):
    ram_gb: int
    gpu_score: int


repository = ResilientGameRepository(
    primary_repository=SteamGameRepository(),
    fallback_repository=InMemoryGameRepository(),
)
search_games = SearchGames(repository)

requirements_repository = InMemoryGameRequirementsRepository()
estimate_compatibility = EstimateCompatibility(requirements_repository)


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/games/search")
def search_games_endpoint(
    q: str = Query(..., min_length=1),
):
    games = search_games.execute(q)

    return [
        {
            "id": game.id,
            "name": game.name,
            "prices": game.prices,
            "unavailable_sources": game.unavailable_sources,
        }
        for game in games
    ]


@app.post("/games/{game_id}/compatibility")
def estimate_compatibility_endpoint(
    game_id: int,
    request: CompatibilityRequest,
):
    return estimate_compatibility.execute(
        game_id=game_id,
        ram_gb=request.ram_gb,
        gpu_score=request.gpu_score,
    )