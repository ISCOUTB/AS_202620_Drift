import logging
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.application.usecases.estimate_compatibility import EstimateCompatibility
from app.application.usecases.search_games import SearchGames
from app.application.usecases.sync_playstation_catalog import SyncPlayStationCatalog
from app.infrastructure.external.playstation.playstation_game_catalog_source import (
    PlayStationGameCatalogSource,
)
from app.infrastructure.external.steam.steam_game_repository import (
    SteamGameRepository,
)
from app.infrastructure.persistence.combined_game_repository import (
    CombinedGameRepository,
)
from app.infrastructure.persistence.in_memory_game_repository import InMemoryGameRepository
from app.infrastructure.persistence.in_memory_playstation_catalog import (
    InMemoryPlayStationCatalog,
)
from app.infrastructure.persistence.in_memory_game_requirements_repository import (
    InMemoryGameRequirementsRepository,
)
from app.infrastructure.persistence.resilient_game_repository import (
    ResilientGameRepository,
)

app = FastAPI(
    title="DRIFT API",
    version="1.0.0",
)
logger = logging.getLogger(__name__)

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


playstation_catalog = InMemoryPlayStationCatalog()
repository = CombinedGameRepository(
    primary_repository=ResilientGameRepository(
        primary_repository=SteamGameRepository(),
        fallback_repository=InMemoryGameRepository(),
    ),
    secondary_repository=playstation_catalog,
)
search_games = SearchGames(repository)
sync_playstation_catalog = SyncPlayStationCatalog(
    source=PlayStationGameCatalogSource(),
    catalog=playstation_catalog,
)

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


@app.post("/games/sync/playstation")
def sync_playstation_catalog_endpoint():
    try:
        return sync_playstation_catalog.execute()
    except httpx.HTTPError as error:
        logger.exception("No fue posible actualizar el catálogo de PlayStation")
        status_code = (
            error.response.status_code
            if isinstance(error, httpx.HTTPStatusError)
            else None
        )
        raise HTTPException(
            status_code=503,
            detail={
                "source": "playstation",
                "reason": str(error),
                "http_status": status_code,
                "local_data_preserved": True,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
            },
        ) from error


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
