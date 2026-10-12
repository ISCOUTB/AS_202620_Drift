import os
from datetime import datetime, timezone
from time import perf_counter

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from pydantic import BaseModel, Field, StrictInt

from app.application.usecases.estimate_compatibility import (
    EstimateCompatibility,
)
from app.application.usecases.list_hardware_catalogue import (
    ListHardwareCatalogue,
)
from app.application.usecases.search_games import SearchGames
from app.application.usecases.sync_playstation_catalog import (
    SyncPlayStationCatalog,
)

from app.domain.services.cpu_classifier import classify_cpu, cpu_level_from_score
from app.domain.services.gpu_classifier import classify_gpu, level_from_score

from app.infrastructure.external.cheapshark.cheapshark_game_repository import (
    CheapSharkGameRepository,
)

from app.infrastructure.external.exchange.open_exchange_rate_provider import (
    OpenExchangeRateProvider,
)

from app.infrastructure.external.playstation.playstation_game_catalog_source import (
    PlayStationGameCatalogSource,
)

from app.infrastructure.external.steam.steam_game_repository import (
    SteamGameRepository,
)

from app.infrastructure.external.steam.steam_game_requirements_repository import (
    SteamGameRequirementsRepository,
)

from app.infrastructure.observability import (
    SearchMetrics,
    configure_structured_logger,
    log_event,
)

from app.infrastructure.persistence.combined_game_repository import (
    CombinedGameRepository,
)

from app.infrastructure.persistence.fallback_game_requirements_repository import (
    FallbackGameRequirementsRepository,
)

from app.infrastructure.persistence.in_memory_game_repository import (
    InMemoryGameRepository,
)

from app.infrastructure.persistence.in_memory_game_requirements_repository import (
    InMemoryGameRequirementsRepository,
)

from app.infrastructure.persistence.in_memory_playstation_catalog import (
    InMemoryPlayStationCatalog,
)

from app.infrastructure.persistence.json_hardware_benchmark_repository import (
    cpu_benchmark_repository,
    gpu_benchmark_repository,
)

from app.infrastructure.persistence.resilient_game_repository import (
    ResilientGameRepository,
)


app = FastAPI(
    title="DRIFT API",
    version="1.0.0",
)


logger = configure_structured_logger()
search_metrics = SearchMetrics()


allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:3000",
    ).split(",")
    if origin.strip()
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CompatibilityRequest(BaseModel):
    ram_gb: StrictInt
    gpu_score: StrictInt
    storage_gb: Optional[StrictInt] = None
    gpu_name: Optional[str] = Field(default=None, max_length=120)
    cpu_score: Optional[StrictInt] = None
    cpu_name: Optional[str] = Field(default=None, max_length=120)


exchange_rates = OpenExchangeRateProvider()


playstation_source = PlayStationGameCatalogSource(
    exchange_rates=exchange_rates,
)


playstation_catalog = InMemoryPlayStationCatalog(
    search_source=playstation_source,
)


repository = CombinedGameRepository(
    primary_repository=CombinedGameRepository(
        primary_repository=ResilientGameRepository(
            primary_repository=SteamGameRepository(),
            fallback_repository=InMemoryGameRepository(),
        ),
        secondary_repository=CheapSharkGameRepository(
            exchange_rates=exchange_rates,
        ),
        secondary_name="CheapShark",
    ),
    secondary_repository=playstation_catalog,
    secondary_name="PlayStation",
)


search_games = SearchGames(repository)


sync_playstation_catalog = SyncPlayStationCatalog(
    source=playstation_source,
    catalog=playstation_catalog,
)


# Primero los requisitos curados por el equipo; para el resto, Steam.
requirements_repository = FallbackGameRequirementsRepository([
    InMemoryGameRequirementsRepository(),
    SteamGameRequirementsRepository(),
])

gpu_benchmarks = gpu_benchmark_repository()
cpu_benchmarks = cpu_benchmark_repository()

estimate_compatibility = EstimateCompatibility(
    requirements_repository,
    gpu_benchmarks,
    cpu_benchmarks,
)

list_gpu_catalogue = ListHardwareCatalogue(
    gpu_benchmarks,
    classify_gpu,
    level_from_score,
)

list_cpu_catalogue = ListHardwareCatalogue(
    cpu_benchmarks,
    classify_cpu,
    cpu_level_from_score,
)


@app.get("/")
def root():
    return {
        "status": "ok"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


@app.get("/metrics")
def metrics():
    return {
        "search_latency": search_metrics.snapshot(),
        "source_degradation": search_metrics.degradation_snapshot(),
    }


@app.get("/hardware/gpus")
def list_graphics_cards():
    return list_gpu_catalogue.execute()


@app.get("/hardware/cpus")
def list_processors():
    return list_cpu_catalogue.execute()


PLAYSTATION_COMPATIBILITY_IDS = {
    "UP2061-NPUB31077_00-PORTAL2DIGITAL01": 620,
}


@app.get("/games/search")
def search_games_endpoint(
    q: str = Query(..., min_length=1),
):
    started_at = perf_counter()

    try:
        games = search_games.execute(q)
        results = []

        for game in games:
            raw_id = str(game.id)

            if raw_id.isdecimal():
                compatibility_id = int(raw_id)
            else:
                compatibility_id = PLAYSTATION_COMPATIBILITY_IDS.get(
                    raw_id
                )

           
            if compatibility_id is None:
                continue

            results.append({
                "id": str(compatibility_id),
                "name": game.name,
                "prices": game.prices,
                "unavailable_sources": game.unavailable_sources,
                "image": game.image,
                "links": game.links,
            })

    except Exception:
        log_event(
            logger,
            "search_failed",
            query_length=len(q),
        )
        raise

    duration_ms = (
        perf_counter() - started_at
    ) * 1000

    unavailable_sources = sorted({
        source
        for game in games
        for source in game.unavailable_sources
    })

    search_metrics.record_search(
        duration_ms,
        unavailable_sources,
    )

    log_event(
        logger,
        "search_completed",
        duration_ms=round(
            duration_ms,
            2,
        ),
        results_count=len(results),
        unavailable_sources=unavailable_sources,
    )

    return results


@app.post("/games/sync/playstation")
def sync_playstation_catalog_endpoint():

    try:
        return sync_playstation_catalog.execute()

    except httpx.HTTPError as error:

        logger.exception(
            "No fue posible actualizar "
            "el catálogo de PlayStation"
        )

        status_code = (
            error.response.status_code
            if isinstance(
                error,
                httpx.HTTPStatusError,
            )
            else None
        )

        raise HTTPException(
            status_code=503,
            detail={
                "source": "playstation",
                "reason": str(error),
                "http_status": status_code,
                "local_data_preserved": True,
                "occurred_at": (
                    datetime.now(
                        timezone.utc
                    ).isoformat()
                ),
            },
        ) from error


@app.post(
    "/games/{game_id}/compatibility"
)
def estimate_compatibility_endpoint(
    game_id: int,
    request: CompatibilityRequest,
):
    return estimate_compatibility.execute(
        game_id=game_id,
        ram_gb=request.ram_gb,
        gpu_score=request.gpu_score,
        storage_gb=request.storage_gb,
        gpu_name=request.gpu_name,
        cpu_name=request.cpu_name,
        cpu_score=request.cpu_score,
    )
