#!/usr/bin/env python3
"""
S12 — Medición de p95 y plazo total con Steam degradado.

Todas las respuestas HTTP son simuladas: no hay llamadas a Steam, CheapShark
ni PlayStation. Las latencias que se miden son las del código de DRIFT
(reintentos, backoff, timeouts, plazo total, concurrencia) frente a un
upstream de laboratorio; NO son mediciones de producción.

CRITERIO DE ACEPTACIÓN (fijado antes de ejecutar; no hay un SLO acordado, por
lo que es una HIPÓTESIS DE LABORATORIO heredada del umbral del escenario E6):

  PLAZO_TOTAL_S = 5.0   plazo total objetivo de una búsqueda
  C1  p95 de la latencia total <= PLAZO_TOTAL_S en cada escenario.
  C2  cumplimiento del plazo (fracción de búsquedas <= PLAZO_TOTAL_S) >= 99 %.
  C3  ninguna búsqueda termina en excepción (la degradación se resuelve con
      el respaldo y el aviso `unavailable_sources`, no con un error).
  C4  en el escenario «normal» no hay búsquedas degradadas.

Un escenario cumple si cumple C1, C2 y C3 (y C4 si es el normal). Los
percentiles usan el método del rango más cercano; el p95 solo se informa con
al menos 20 muestras y el p99 con al menos 100.

Se comparan dos configuraciones del mismo código:
  s11  RetryPolicy() sin plazo total (comportamiento de S11).
  s12  RetryPolicy(total_deadline_seconds=DEFAULT_TOTAL_DEADLINE_SECONDS).

Cada búsqueda usa un repositorio nuevo (sin caché): mide el camino frío, el
peor caso. Con caché caliente la latencia sería menor.

Uso (desde la raíz del repositorio):

  python scripts/s12_latencia_steam.py [--samples 100] [--concurrency 20]
         [--seed 12] [--only normal,lento] [--out docs/evidencias/s12-resultados]

El resultado es reproducible en distribución, no bit a bit: los hilos cambian
el orden en que se sortean las latencias.
"""

import argparse
import json
import logging
import math
import platform
import random
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

import httpx  # noqa: E402

from app.application.usecases.search_games import SearchGames  # noqa: E402
from app.domain.ports.exchange_rate_provider import ExchangeRateProvider  # noqa: E402
from app.infrastructure.external.cheapshark.cheapshark_game_repository import (  # noqa: E402
    CheapSharkGameRepository,
)
from app.infrastructure.external.playstation.playstation_game_catalog_source import (  # noqa: E402
    PlayStationGameCatalogSource,
)
from app.infrastructure.external.resilient_http import RetryPolicy  # noqa: E402
from app.infrastructure.external.steam.steam_game_repository import (  # noqa: E402
    DEFAULT_TOTAL_DEADLINE_SECONDS,
    SteamGameRepository,
)
from app.infrastructure.persistence.combined_game_repository import (  # noqa: E402
    CombinedGameRepository,
)
from app.infrastructure.persistence.in_memory_game_repository import (  # noqa: E402
    InMemoryGameRepository,
)
from app.infrastructure.persistence.in_memory_playstation_catalog import (  # noqa: E402
    InMemoryPlayStationCatalog,
)
from app.infrastructure.persistence.resilient_game_repository import (  # noqa: E402
    ResilientGameRepository,
)

PLAZO_TOTAL_S = 5.0
MIN_COMPLIANCE = 0.99
QUERY = "Minecraft"  # existe en el respaldo en memoria: la degradación es visible

CONFIGS = {
    "s11": lambda: RetryPolicy(),
    "s12": lambda: RetryPolicy(
        total_deadline_seconds=DEFAULT_TOTAL_DEADLINE_SECONDS
    ),
}

# Escenarios de Steam. `outcome(rng)` devuelve ("ok", latencia_s),
# ("hang", None) —no responde: agota el timeout— o ("http", estado).
SCENARIOS = {
    "normal": lambda rng: ("ok", rng.uniform(0.10, 0.25)),
    "lento": lambda rng: ("ok", rng.uniform(2.0, 3.6)),
    "intermitente": lambda rng: (
        lambda x: ("hang", None)
        if x < 0.30
        else ("http", 503)
        if x < 0.40
        else ("ok", rng.uniform(0.10, 0.25))
    )(rng.random()),
    "no_disponible_timeout": lambda rng: ("hang", None),
    "no_disponible_503": lambda rng: ("http", 503),
}


def percentile(values, p):
    """Rango más cercano. `None` si no hay muestras."""

    if not values:
        return None

    ordered = sorted(values)
    rank = max(1, math.ceil(p / 100 * len(ordered)))

    return ordered[rank - 1]


def summarize(values):
    """p50/p95/p99 con la regla de muestras mínimas; siempre incluye `n`."""

    n = len(values)

    return {
        "n": n,
        "p50": percentile(values, 50) if n >= 1 else None,
        "p95": percentile(values, 95) if n >= 20 else None,
        "p99": percentile(values, 99) if n >= 100 else None,
        "max": max(values) if values else None,
    }


class _Rate(ExchangeRateProvider):
    def usd_to_cop(self) -> float:
        return 4000.0


class _RetryLog(logging.Handler):
    """Cuenta los eventos de `resilient_http` sin escribir nada."""

    def __init__(self):
        super().__init__(level=logging.INFO)
        self.events = Counter()
        self._lock = threading.Lock()

    def emit(self, record):
        message = record.getMessage()
        fields = getattr(record, "fields", {})

        with self._lock:
            if message == "external_retry":
                self.events["retries"] += 1
            elif message == "external_request_failed":
                self.events[f"failed_{fields.get('reason')}"] += 1


class FakeUpstream:
    """HTTP simulado. Steam sigue el escenario; el resto responde rápido."""

    def __init__(self, scenario, seed):
        self._scenario = SCENARIOS[scenario]
        self._rng = random.Random(seed)
        self._lock = threading.Lock()
        self.steam_calls = []  # (latencia_s, resultado)
        self.counts = Counter()

    def get(self, url, params=None, headers=None, timeout=None):
        if "store.steampowered.com" in url:
            return self._steam(url, timeout)

        time.sleep(0.02)

        if url.endswith("/deals"):
            return _response(url, [])

        if url.endswith("/stores"):
            return _response(url, [])

        return _response(url, {"links": []})

    def _steam(self, url, timeout):
        with self._lock:
            kind, value = self._scenario(self._rng)
            self.counts["steam_requests"] += 1

        started = time.monotonic()

        if kind == "hang" or (kind == "ok" and value > timeout):
            time.sleep(timeout)
            self._record(started, "timeout")
            raise httpx.ReadTimeout("simulado")

        if kind == "http":
            time.sleep(0.02)
            self._record(started, f"http_{value}")

            return _response(url, {}, status=value)

        time.sleep(value)
        self._record(started, "ok")

        if "storesearch" in url:
            return _response(url, {"items": [{"id": 1, "name": "Minecraft"}]})

        return _response(
            url,
            {"1": {"success": True, "data": {"price_overview": {"final": 11990000}}}},
        )

    def _record(self, started, result):
        elapsed = time.monotonic() - started

        with self._lock:
            self.steam_calls.append(elapsed)
            self.counts[f"steam_{result}"] += 1


def _response(url, payload, status=200):
    return httpx.Response(
        status,
        json=payload,
        request=httpx.Request("GET", url),
    )


def _build(policy):
    steam = SteamGameRepository(policy=policy)
    playstation = PlayStationGameCatalogSource(exchange_rates=_Rate())

    return SearchGames(
        CombinedGameRepository(
            primary_repository=CombinedGameRepository(
                primary_repository=ResilientGameRepository(
                    primary_repository=steam,
                    fallback_repository=InMemoryGameRepository(),
                ),
                secondary_repository=CheapSharkGameRepository(_Rate()),
                secondary_name="CheapShark",
            ),
            secondary_repository=InMemoryPlayStationCatalog(
                search_source=playstation
            ),
            secondary_name="PlayStation",
        )
    )


def run_scenario(scenario, config, samples, concurrency, seed):
    upstream = FakeUpstream(scenario, seed)
    log = _RetryLog()
    logger = logging.getLogger("drift")
    previous_level, previous_propagate = logger.level, logger.propagate
    logger.setLevel(logging.INFO)
    logger.addHandler(log)
    logger.propagate = False
    original_get = httpx.get
    httpx.get = upstream.get

    totals, errors, degraded = [], 0, 0
    guard = threading.Lock()

    def one_search(_):
        nonlocal errors, degraded
        policy = CONFIGS[config]()
        search = _build(policy)
        started = time.monotonic()

        try:
            games = search.execute(QUERY)
            failed = False
        except Exception:  # C3: cualquier excepción cuenta como error
            games, failed = [], True

        elapsed = time.monotonic() - started

        with guard:
            totals.append(elapsed)

            if failed:
                errors += 1
            elif any("Steam" in g.unavailable_sources for g in games):
                degraded += 1

    try:
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            list(pool.map(one_search, range(samples)))
    finally:
        httpx.get = original_get
        logger.removeHandler(log)
        logger.setLevel(previous_level)
        logger.propagate = previous_propagate

    within = sum(1 for t in totals if t <= PLAZO_TOTAL_S)
    compliance = within / len(totals)
    total = summarize(totals)

    c1 = total["p95"] is not None and total["p95"] <= PLAZO_TOTAL_S
    c2 = compliance >= MIN_COMPLIANCE
    c3 = errors == 0
    c4 = degraded == 0 if scenario == "normal" else True

    return {
        "scenario": scenario,
        "config": config,
        "samples": samples,
        "total_seconds": total,
        "steam_call_seconds": summarize(upstream.steam_calls),
        "steam_requests": upstream.counts["steam_requests"],
        "steam_outcomes": {
            k.removeprefix("steam_"): v
            for k, v in sorted(upstream.counts.items())
            if k != "steam_requests"
        },
        "retries": log.events["retries"],
        "terminal_failures": {
            k.removeprefix("failed_"): v
            for k, v in sorted(log.events.items())
            if k.startswith("failed_")
        },
        "searches_with_error": errors,
        "searches_degraded_steam": degraded,
        "deadline_compliance": round(compliance, 4),
        "criteria": {"C1_p95": c1, "C2_compliance": c2, "C3_no_errors": c3, "C4_normal_not_degraded": c4},
        "passes": c1 and c2 and c3 and c4,
    }


def _fmt(value):
    return "n/a" if value is None else f"{value:.2f}"


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--samples", type=int, default=100)
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--seed", type=int, default=12)
    parser.add_argument("--only", default=",".join(SCENARIOS))
    parser.add_argument("--configs", default="s11,s12")
    parser.add_argument("--out", default=str(ROOT / "docs/evidencias/s12-resultados"))
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    results = []

    for scenario in args.only.split(","):
        for config in args.configs.split(","):
            print(f"-> {scenario} / {config} ...", flush=True)
            result = run_scenario(
                scenario, config, args.samples, args.concurrency, args.seed
            )
            results.append(result)
            t, c = result["total_seconds"], result["steam_call_seconds"]
            print(
                f"   total p50/p95/p99/max = {_fmt(t['p50'])}/{_fmt(t['p95'])}/"
                f"{_fmt(t['p99'])}/{_fmt(t['max'])} s | llamada Steam p50/p95 = "
                f"{_fmt(c['p50'])}/{_fmt(c['p95'])} s | solicitudes Steam = "
                f"{result['steam_requests']} | reintentos = {result['retries']} | "
                f"plazo cumplido = {result['deadline_compliance']:.0%} | "
                f"degradadas = {result['searches_degraded_steam']} | "
                f"errores = {result['searches_with_error']} | "
                f"{'CUMPLE' if result['passes'] else 'NO CUMPLE'}",
                flush=True,
            )

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "httpx": getattr(httpx, "__version__", "desconocida"),
        },
        "nature": "respuestas HTTP simuladas; no es una medición de producción",
        "criteria": {
            "plazo_total_s": PLAZO_TOTAL_S,
            "min_compliance": MIN_COMPLIANCE,
            "status": "hipótesis de laboratorio (no hay SLO acordado)",
        },
        "parameters": {
            "samples": args.samples,
            "concurrency": args.concurrency,
            "seed": args.seed,
            "query": QUERY,
            "cold_path": True,
        },
        "results": results,
    }

    target = out / "steam-degradado.json"
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Resultados escritos en {target}")


if __name__ == "__main__":
    main()
