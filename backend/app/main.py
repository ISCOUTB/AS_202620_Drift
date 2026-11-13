import os
from datetime import datetime, timezone
from time import perf_counter

import httpx
from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request
from typing import Dict, List, Literal
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.routing import Match
from typing import Optional

from pydantic import BaseModel, Field, StrictInt, field_validator

from app.application.usecases.accounts import Devices, Favorites, Sessions
from app.application.usecases.favorite_alerts import CheckFavoriteAlerts
from app.infrastructure.external.store_current_prices import (
    StoreCurrentPriceSource,
)
from app.application.usecases.estimate_compatibility import (
    EstimateCompatibility,
)
from app.application.usecases.get_price_history import GetPriceHistory
from app.application.usecases.list_hardware_catalogue import (
    ListHardwareCatalogue,
)
from app.application.usecases.recommend_purchase import RecommendPurchase
from app.application.usecases.search_games import SearchGames
from app.domain.model.account import Device, InvalidDevice, PcSpecs
from app.application.usecases.showcase import (
    ExploreGames,
    ListFeaturedGames,
    ListStores,
)
from app.domain.ports.showcase import ExploreQuery
from app.application.usecases.sync_hardware_benchmarks import (
    BenchmarkSyncRejected,
    SyncHardwareBenchmarks,
)
from app.application.usecases.sync_playstation_catalog import (
    CatalogSyncRejected,
    SyncPlayStationCatalog,
)

from app.domain.services.cpu_classifier import classify_cpu, cpu_level_from_score
from app.domain.services.gpu_classifier import classify_gpu, level_from_score

from app.infrastructure.external.cheapshark.cheapshark_game_repository import (
    CheapSharkGameRepository,
)

from app.infrastructure.api.account_routes import (
    AccountSettings,
    build_account_router,
)
from app.infrastructure.external.google.google_identity_provider import (
    GoogleIdentityProvider,
)
from app.infrastructure.persistence.account_repository_factory import (
    build_account_repository,
)

from app.infrastructure.api.security import (
    SlidingWindowRateLimiter,
    client_ip,
    rate_limit_from_env,
    require_admin_token,
)

from app.infrastructure.external.resilient_http import ExternalSourceError
from app.infrastructure.external.exchange.open_exchange_rate_provider import (
    OpenExchangeRateProvider,
)

from app.infrastructure.external.isthereanydeal.itad_client import ItadClient
from app.infrastructure.external.isthereanydeal.itad_game_repository import (
    ItadGameRepository,
)
from app.infrastructure.external.isthereanydeal.itad_price_history_repository import (
    ItadPriceHistoryRepository,
)

from app.infrastructure.external.playstation.playstation_game_catalog_source import (
    PlayStationGameCatalogSource,
)

from app.infrastructure.external.steam.steam_featured_games_source import (
    SteamFeaturedGamesSource,
)
from app.infrastructure.external.steam.steam_game_explorer import (
    SteamGameExplorer,
)
from app.infrastructure.external.steam.steam_store_items import SteamStoreItems
from app.infrastructure.external.steam.steam_game_repository import (
    SteamGameRepository,
)

from app.infrastructure.external.steam.steam_game_requirements_repository import (
    SteamGameRequirementsRepository,
)

from app.infrastructure.external.xbox.xbox_game_repository import (
    XboxGameRepository,
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
    build_hardware_benchmark_store,
    cpu_benchmark_repository,
    cpu_copy,
    gpu_benchmark_repository,
    gpu_copy,
)

from app.infrastructure.persistence.resilient_game_repository import (
    ResilientGameRepository,
)

from app.infrastructure.persistence.source_snapshot_store_factory import (
    build_source_snapshot_store,
)

from app.infrastructure.persistence.stale_fallback_game_repository import (
    StaleFallbackGameRepository,
)


app = FastAPI(
    title="DRIFT API",
    version="1.0.0",
)


def _all_routes(routes):
    """Las rutas de la aplicación, también las de los routers incluidos.

    Desde FastAPI 0.16x, `include_router` guarda el router incluido como un
    solo elemento (`_IncludedRouter`) en lugar de copiar sus rutas. Los
    routers de DRIFT se incluyen sin prefijo, así que sus rutas se comparan
    con la dirección tal cual.
    """

    for route in routes:
        nested = getattr(getattr(route, "original_router", None), "routes", None)

        if nested is not None:
            yield from _all_routes(nested)
        elif hasattr(route, "matches"):
            yield route


@app.exception_handler(405)
async def method_not_allowed(request: Request, exc):
    """`Allow` con todos los métodos de la dirección, no solo los de una ruta.

    Starlette responde con los métodos de la primera ruta que coincide con
    la dirección; si una dirección tiene varias rutas (`GET` y `DELETE` en
    `/auth/me`), el encabezado quedaba incompleto (RFC 9110, 15.5.6).
    """

    methods = set()

    for route in _all_routes(app.router.routes):
        match, _ = route.matches(request.scope)

        if match is Match.PARTIAL:
            methods.update(getattr(route, "methods", None) or ())

    headers = dict(getattr(exc, "headers", None) or {})

    if methods:
        headers["Allow"] = ", ".join(sorted(methods))

    return JSONResponse(
        {"detail": getattr(exc, "detail", "Method Not Allowed")},
        status_code=405,
        headers=headers,
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


# A3 (ADR-0012): límite por cliente en las rutas que llaman a fuentes externas.
rate_limiter = SlidingWindowRateLimiter(limit=rate_limit_from_env())


def _calls_external_sources(request: Request) -> bool:
    path = request.url.path.rstrip("/")

    return (
        request.method == "GET"
        and (
            path.endswith("/games/search")
            or path.endswith("/games/explore")
            or path.endswith("/price-history")
            # Cada inicio de sesión hace una llamada a Google.
            or path.endswith("/auth/google/callback")
            # Revisar los favoritos consulta Steam e IsThereAnyDeal.
            or path.endswith("/favorites/alerts")
        )
    ) or (
        request.method == "POST"
        and (path.endswith("/compatibility") or path.endswith("/recommendation"))
    )


@app.middleware("http")
async def limit_rate(request: Request, call_next):
    if _calls_external_sources(request):
        allowed, retry_after = rate_limiter.check(client_ip(request))

        if not allowed:
            log_event(
                logger,
                "rate_limited",
                path=request.url.path,
                retry_after_seconds=retry_after,
            )

            return JSONResponse(
                status_code=429,
                content={"detail": {"reason": "rate_limited", "retry_after_seconds": retry_after}},
                headers={"Retry-After": str(retry_after)},
            )

    return await call_next(request)


# A9 (ADR-0012, modificado por ADR-0017): solo los orígenes configurados, nunca
# «*». Desde ADR-0017 la sesión viaja en una cookie, así que esos orígenes
# pueden enviar credenciales; PUT y DELETE son para los dispositivos.
# Se agrega después del límite de tasa para que también las respuestas 429
# lleven las cabeceras CORS y el navegador pueda leerlas.
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type"],
)


class CompatibilityRequest(BaseModel):
    ram_gb: StrictInt
    gpu_score: StrictInt
    storage_gb: Optional[StrictInt] = None
    gpu_name: Optional[str] = Field(default=None, max_length=120)
    cpu_score: Optional[StrictInt] = None
    cpu_name: Optional[str] = Field(default=None, max_length=120)


class RecommendationDevice(BaseModel):
    id: Optional[str] = Field(default=None, max_length=80)
    name: str = Field(min_length=1, max_length=40)
    kind: Literal["pc", "playstation", "xbox"]
    specs: Optional[CompatibilityRequest] = None


class RecommendationRequest(BaseModel):
    # Precios que el usuario tiene en pantalla, por tienda, en pesos.
    prices: Dict[str, float] = Field(max_length=60)
    discounts: Dict[str, int] = Field(default_factory=dict, max_length=60)
    devices: List[RecommendationDevice] = Field(
        default_factory=list,
        max_length=10,
    )

    @field_validator("prices")
    @classmethod
    def _valid_prices(cls, prices):
        for store, price in prices.items():
            if not store.strip() or len(store) > 60:
                raise ValueError("Nombre de tienda no válido.")

            if not 0 <= price <= 1_000_000_000:
                raise ValueError("Precio no válido.")

        return prices


exchange_rates = OpenExchangeRateProvider()


playstation_source = PlayStationGameCatalogSource(
    exchange_rates=exchange_rates,
)


playstation_catalog = InMemoryPlayStationCatalog(
    search_source=playstation_source,
)


# ADR-0014 y ADR-0015: copia de respaldo de lo que respondió cada fuente.
# Con DRIFT_DATABASE_URL vive en PostgreSQL; sin ella, en memoria.
snapshot_store = build_source_snapshot_store()

steam_repository = SteamGameRepository()

steam_with_backup = StaleFallbackGameRepository(
    steam_repository,
    "Steam",
    snapshot_store,
)

# Tiendas de PC distintas de Steam. Con DRIFT_ITAD_API_KEY se consultan en
# IsThereAnyDeal, que además entrega el historial de precios. Sin la llave se
# usa CheapShark, que no la necesita, y el historial queda deshabilitado.
itad_api_key = os.getenv("DRIFT_ITAD_API_KEY", "").strip()
itad_client = ItadClient(itad_api_key) if itad_api_key else None

if itad_client is not None:
    pc_stores_name = "IsThereAnyDeal"
    pc_stores = ItadGameRepository(itad_client, exchange_rates)
    price_history_repository = ItadPriceHistoryRepository(
        itad_client,
        exchange_rates,
        steam_prices=steam_repository.price_in_colombia,
    )
else:
    pc_stores_name = "CheapShark"
    pc_stores = CheapSharkGameRepository(
        exchange_rates=exchange_rates,
    )
    price_history_repository = None

pc_stores_with_backup = StaleFallbackGameRepository(
    pc_stores,
    pc_stores_name,
    snapshot_store,
)

get_price_history = GetPriceHistory(price_history_repository)

# Portada: juegos del momento y tiendas conectadas.
# Fichas de Steam (imágenes reales, descripción, precio) para la portada y
# la página «Explorar».
steam_store_items = SteamStoreItems()
list_featured_games = ListFeaturedGames(
    SteamFeaturedGamesSource(store_items=steam_store_items)
)
explore_games = ExploreGames(SteamGameExplorer(steam_store_items))
list_stores = ListStores(pc_stores, pc_stores_name)

playstation_with_backup = StaleFallbackGameRepository(
    playstation_catalog,
    "PlayStation",
    snapshot_store,
)


xbox_with_backup = StaleFallbackGameRepository(
    XboxGameRepository(
        exchange_rates=exchange_rates,
    ),
    "Xbox",
    snapshot_store,
)


# Cada nivel lanza su fuente secundaria en un hilo antes de consultar la
# principal, así que las cuatro fuentes se consultan a la vez.
repository = CombinedGameRepository(
    primary_repository=CombinedGameRepository(
        primary_repository=CombinedGameRepository(
            primary_repository=ResilientGameRepository(
                primary_repository=steam_with_backup,
                fallback_repository=InMemoryGameRepository(),
            ),
            secondary_repository=pc_stores_with_backup,
            secondary_name=pc_stores_name,
            secondary_last_known=pc_stores_with_backup.last_known,
        ),
        secondary_repository=playstation_with_backup,
        secondary_name="PlayStation",
        secondary_last_known=playstation_with_backup.last_known,
    ),
    secondary_repository=xbox_with_backup,
    secondary_name="Xbox",
    secondary_last_known=xbox_with_backup.last_known,
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

# ADR-0018: con base de datos, los puntajes se leen de PostgreSQL; la copia
# JSON queda como origen de la carga y como respaldo si la base no responde.
hardware_benchmark_store = build_hardware_benchmark_store()

gpu_benchmarks = gpu_benchmark_repository(hardware_benchmark_store)
cpu_benchmarks = cpu_benchmark_repository(hardware_benchmark_store)


def _reload_hardware_benchmarks() -> None:
    gpu_benchmarks.reload()
    cpu_benchmarks.reload()


sync_hardware_benchmarks = SyncHardwareBenchmarks(
    sources={"gpu": gpu_copy, "cpu": cpu_copy},
    store=hardware_benchmark_store,
    on_loaded=_reload_hardware_benchmarks,
)

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


# Cuentas y dispositivos (ADR-0017). Sin el cliente de Google configurado, el
# inicio de sesión queda deshabilitado y el resto de DRIFT funciona igual.
google_client_id = os.getenv("DRIFT_GOOGLE_CLIENT_ID", "").strip()
google_client_secret = os.getenv("DRIFT_GOOGLE_CLIENT_SECRET", "").strip()
google_redirect_uri = os.getenv(
    "DRIFT_GOOGLE_REDIRECT_URI",
    "http://localhost:8000/auth/google/callback",
).strip()

if google_client_id and google_client_secret:
    account_repository = build_account_repository()
    account_sessions = Sessions(
        account_repository,
        GoogleIdentityProvider(
            google_client_id,
            google_client_secret,
            google_redirect_uri,
        ),
    )
    account_devices = Devices(account_repository)
    account_favorites = Favorites(account_repository)
    # ADR-0021: el precio de hoy de los favoritos, solo tiendas de PC.
    account_favorite_alerts = CheckFavoriteAlerts(
        account_repository,
        StoreCurrentPriceSource(
            steam_repository.price_in_colombia,
            itad_client,
            exchange_rates,
        ),
    )
else:
    account_sessions = None
    account_devices = None
    account_favorites = None
    account_favorite_alerts = None

app.include_router(
    build_account_router(
        account_sessions,
        account_devices,
        AccountSettings(
            frontend_url=os.getenv(
                "DRIFT_FRONTEND_URL",
                allowed_origins[0] if allowed_origins else "http://localhost:3000",
            ).strip(),
            allowed_origins=allowed_origins,
            secure_cookies=google_redirect_uri.startswith("https://"),
        ),
        account_favorites,
        account_favorite_alerts,
    )
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


@app.get("/metrics", dependencies=[Depends(require_admin_token)])
def metrics():
    return {
        "search_latency": search_metrics.snapshot(),
        "source_degradation": search_metrics.degradation_snapshot(),
        "source_backup": search_metrics.backup_snapshot(),
        "itad_quota": (
            itad_client.quota_snapshot() if itad_client is not None else None
        ),
    }


@app.post(
    "/hardware/benchmarks/sync",
    dependencies=[Depends(require_admin_token)],
)
def sync_hardware_benchmarks_endpoint(request: Request):
    """Vuelve a cargar los puntajes desde su copia privada (ADR-0018)."""

    log_event(
        logger,
        "admin_benchmark_sync_requested",
        client_ip=client_ip(request),
    )

    try:
        result = sync_hardware_benchmarks.execute()
    except BenchmarkSyncRejected as error:
        raise HTTPException(
            status_code=503,
            detail={
                "reason": "empty_benchmark_copy",
                "kind": error.kind,
                "stored_data_preserved": True,
            },
        ) from error
    except Exception as error:  # noqa: BLE001  fallo de la base de datos
        log_event(
            logger,
            "admin_benchmark_sync_failed",
            error=type(error).__name__,
        )

        raise HTTPException(
            status_code=503,
            detail={
                "reason": "benchmark_store_unavailable",
                "stored_data_preserved": True,
            },
        ) from error

    log_event(logger, "admin_benchmark_sync_completed", loaded=result["loaded"])

    return result


@app.get("/hardware/gpus")
def list_graphics_cards():
    return list_gpu_catalogue.execute()


@app.get("/hardware/cpus")
def list_processors():
    return list_cpu_catalogue.execute()


@app.get("/games/featured")
def featured_games_endpoint(
    category: Optional[
        Literal["Acción", "Aventura", "Carreras", "Deportes", "RPG", "Estrategia"]
    ] = Query(default=None),
):
    """Juegos más vendidos del momento; la lista cambia con las ventas."""

    return {
        "category": category,
        "source": "Steam",
        "items": [
            {
                "id": game.id,
                "name": game.name,
                "image": game.image,
                "hero": game.hero,
                "header": game.header,
            }
            for game in list_featured_games.execute(category)
        ],
    }


def _explore_game_json(game):
    return {
        "id": game.id,
        "name": game.name,
        "image": game.image,
        "hero": game.hero,
        "header": game.header,
        "capsule": game.capsule,
        "description": game.description,
        "tags": list(game.tags),
        "release_date": game.release_date.isoformat() if game.release_date else None,
        "developers": list(game.developers),
        "review": game.review,
        "review_percent": game.review_percent,
        "price": game.price,
        "original_price": game.original_price,
        "discount": game.discount,
        "is_free": game.is_free,
    }


@app.get("/games/explore")
def explore_games_endpoint(
    genre: Optional[
        Literal[
            "accion", "aventura", "rol", "estrategia", "simulacion",
            "deportes", "carreras", "terror", "casuales",
        ]
    ] = Query(default=None),
    tag: Optional[
        List[
            Literal[
                "un-jugador", "multijugador", "cooperativo", "mundo-abierto",
                "buena-trama", "indie", "anime", "pixelados", "fantasia",
                "ciencia-ficcion", "supervivencia", "por-turnos",
            ]
        ]
    ] = Query(default=None, max_length=6),
    sort: Literal["populares", "valorados", "precio-asc", "precio-desc"] = "populares",
    price: Literal["todos", "gratis", "hasta-40000", "hasta-100000", "ofertas"] = "todos",
    page: int = Query(default=1, ge=1, le=20),
):
    """Una página del catálogo de Steam con la ficha de cada juego."""

    try:
        answer = explore_games.execute(
            ExploreQuery(
                genre=genre,
                tags=tuple(tag or ()),
                sort=sort,
                price=price,
                page=page,
            )
        )
    except (httpx.HTTPError, ExternalSourceError) as error:
        log_event(
            logger,
            "explore_failed",
            reason=getattr(error, "reason", "error"),
        )

        raise HTTPException(
            status_code=503,
            detail={"source": "Steam", "reason": "source_unavailable"},
        ) from error

    return {
        "genre": genre,
        "page": page,
        "has_more": answer.has_more,
        "items": [_explore_game_json(game) for game in answer.items],
    }


@app.get("/stores")
def stores_endpoint():
    """Todas las tiendas cuyos precios compara DRIFT."""

    return list_stores.execute()


@app.get("/games/search")
def search_games_endpoint(
    q: str = Query(..., min_length=1),
    platform: Optional[List[Literal["PC", "PlayStation", "Xbox"]]] = Query(
        default=None,
        description="Solo tiendas de estas plataformas. Se puede repetir.",
    ),
):
    started_at = perf_counter()

    try:
        games = search_games.execute(q, platforms=platform)
        results = []

        for game in games:
            raw_id = str(game.id)

            # Un juego que viene de Steam conserva su identificador numérico,
            # que es el que usa la estimación de compatibilidad. Uno que solo
            # existe en otra tienda conserva el identificador de esa tienda.
            if not raw_id.isdecimal():
                # Sin precio no hay nada que comparar ni dónde comprarlo.
                if not game.prices:
                    continue

            results.append({
                "id": raw_id,
                "name": game.name,
                "prices": game.prices,
                "unavailable_sources": game.unavailable_sources,
                "cached_sources": game.cached_sources,
                "image": game.image,
                "links": game.links,
                "discounts": game.discounts,
                "platforms": game.platforms,
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

    cached_sources = sorted({
        source
        for game in games
        for source in game.cached_sources
    })

    search_metrics.record_search(
        duration_ms,
        unavailable_sources,
        cached_sources,
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
        cached_sources=cached_sources,
    )

    return results


def _sync_failed(reason: str, http_status):
    """503 del contrato: la sincronización falló y el catálogo local se conserva."""

    return HTTPException(
        status_code=503,
        detail={
            "source": "playstation",
            "reason": reason,
            "http_status": http_status,
            "local_data_preserved": True,
            "occurred_at": (
                datetime.now(
                    timezone.utc
                ).isoformat()
            ),
        },
    )


@app.post(
    "/games/sync/playstation",
    dependencies=[Depends(require_admin_token)],
)
def sync_playstation_catalog_endpoint(request: Request):

    # A10: queda registro de cada sincronización autorizada y de su origen.
    log_event(
        logger,
        "admin_catalog_sync_requested",
        source="playstation",
        client_ip=client_ip(request),
    )

    try:
        result = sync_playstation_catalog.execute()
        log_event(
            logger,
            "admin_catalog_sync_completed",
            source="playstation",
            games_loaded=result.get("games_loaded") if isinstance(result, dict) else None,
        )
        return result

    except CatalogSyncRejected as error:

        logger.warning(
            "Sincronización de PlayStation rechazada: %s",
            error.reason,
        )

        raise _sync_failed(error.reason, None) from error

    except (httpx.HTTPError, ExternalSourceError) as error:

        logger.exception(
            "No fue posible actualizar "
            "el catálogo de PlayStation"
        )

        if isinstance(error, httpx.HTTPStatusError):
            status_code = error.response.status_code
        elif isinstance(error, ExternalSourceError):
            status_code = error.status_code
        else:
            status_code = None

        raise _sync_failed(str(error), status_code) from error


def _price_point(point):
    if point is None:
        return None

    return {
        "date": point.date.isoformat(),
        "store": point.store,
        "price": point.price,
        "discount": point.discount,
    }


@app.get("/games/{game_id}/price-history")
def price_history_endpoint(
    game_id: str = Path(..., pattern=r"^[A-Za-z0-9_-]{1,80}$"),
):
    try:
        answer = get_price_history.execute(game_id)
    except (httpx.HTTPError, ExternalSourceError) as error:
        log_event(
            logger,
            "price_history_failed",
            reason=getattr(error, "reason", "error"),
        )

        raise HTTPException(
            status_code=503,
            detail={
                "source": "IsThereAnyDeal",
                "reason": "source_unavailable",
            },
        ) from error

    history = answer.history

    if history is None:
        return {
            "game_id": game_id,
            "available": False,
            "reason": answer.reason,
            "source": "IsThereAnyDeal",
            "currency": "COP",
            "since": None,
            "cached_at": None,
            "current": None,
            "lowest": None,
            "steam_best_discount": None,
            "points": [],
        }

    return {
        "game_id": game_id,
        "available": True,
        "reason": None,
        "source": "IsThereAnyDeal",
        "currency": "COP",
        "since": history.since.isoformat(),
        "cached_at": (
            history.cached_at.isoformat() if history.cached_at else None
        ),
        "current": _price_point(history.current),
        "lowest": _price_point(history.lowest),
        "steam_best_discount": (
            {
                "date": history.steam_best_discount.date.isoformat(),
                "discount": history.steam_best_discount.discount,
            }
            if history.steam_best_discount
            else None
        ),
        "points": [_price_point(point) for point in history.points],
    }


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


recommend_purchase = RecommendPurchase(estimate_compatibility)


def _option_json(option):
    if option is None:
        return None

    device = option.device

    return {
        "store": option.store,
        "platform": option.platform,
        "price": option.price,
        "discount": option.discount,
        "experience": option.experience,
        "device": (
            {"id": device.device_id, "name": device.name, "kind": device.kind}
            if device
            else None
        ),
    }


@app.post("/games/{game_id}/recommendation")
def recommend_purchase_endpoint(
    request: RecommendationRequest,
    game_id: str = Path(..., pattern=r"^[A-Za-z0-9_-]{1,80}$"),
):
    try:
        devices = [
            Device(
                id=device.id or f"local-{index}",
                user_id="",
                name=device.name,
                kind=device.kind,
                specs=(
                    PcSpecs(**device.specs.model_dump()) if device.specs else None
                ),
            )
            for index, device in enumerate(request.devices)
        ]
    except InvalidDevice as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    answer = recommend_purchase.execute(
        game_id,
        request.prices,
        request.discounts,
        devices,
    )

    return {
        "game_id": game_id,
        "uses_devices": answer.uses_devices,
        "recommended": _option_json(answer.best),
        "reason": answer.reason,
        "price_difference": answer.price_difference,
        "alternatives": [_option_json(option) for option in answer.alternatives],
        "excluded": [
            {
                "device": {
                    "id": item.device.device_id,
                    "name": item.device.name,
                    "kind": item.device.kind,
                },
                "reason": item.reason,
            }
            for item in answer.excluded
        ],
    }
