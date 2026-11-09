// Medición S14 del escenario E1: búsqueda con 50 usuarios concurrentes.
// Umbral de arc42 §10.2: p95 <= 3 s. Procedimiento: docs/evidencias/s14-e1-medicion.md
//
//   k6 run -e MODO=distintas -e SALIDA=resultado.json scripts/k6_s14_e1_busqueda.js
//
// MODO=distintas: una consulta distinta por usuario (ninguna comparte caché).
// MODO=misma: los 50 usuarios buscan lo mismo, como la línea base de E1.

import http from "k6/http";
import { check } from "k6";
import { Counter, Trend } from "k6/metrics";

const BASE_URL = __ENV.BASE_URL || "https://drift.iscoutb.dev/api";
const MODO = __ENV.MODO || "distintas";
const SALIDA = __ENV.SALIDA || "s14-resultado.json";

const TITULOS = [
  "Portal 2", "Hades", "Celeste", "Stardew Valley", "Hollow Knight",
  "Terraria", "Elden Ring", "Dark Souls III", "Sekiro", "Cuphead",
  "The Witcher 3", "Cyberpunk 2077", "Red Dead Redemption 2", "Baldur's Gate 3", "Disco Elysium",
  "Doom Eternal", "Half-Life 2", "Left 4 Dead 2", "Counter-Strike", "Team Fortress 2",
  "Skyrim", "Fallout 4", "Fallout New Vegas", "Mass Effect", "Dragon Age",
  "Civilization VI", "Cities Skylines", "Factorio", "RimWorld", "Subnautica",
  "Slay the Spire", "Dead Cells", "Ori and the Blind Forest", "Inside", "Limbo",
  "Resident Evil 4", "Devil May Cry 5", "Monster Hunter World", "Street Fighter 6", "Tekken 8",
  "Sonic Mania", "Tomb Raider", "Hitman 3", "Control", "Alan Wake 2",
  "Forza Horizon 5", "Euro Truck Simulator 2", "Rocket League", "Among Us", "Minecraft",
];

const busquedaMs = new Trend("busqueda_ms", true);
const redMs = new Trend("red_health_ms", true);
const estadosOk = new Counter("estado_200");
const estados429 = new Counter("estado_429");
const estadosOtros = new Counter("estado_otro");
const vacias = new Counter("respuestas_vacias");
const sinSteam = new Counter("sin_steam");
const sinCheapShark = new Counter("sin_cheapshark");
const sinPlayStation = new Counter("sin_playstation");

export const options = {
  userAgent: "DRIFT-S14-medicion/1.0 (proyecto academico AS_202620 UTB)",
  scenarios: {
    e1_busqueda: {
      executor: "per-vu-iterations",
      vus: 50,
      iterations: 1,
      maxDuration: "120s",
    },
  },
  thresholds: {
    busqueda_ms: ["p(95)<=3000"],
  },
  summaryTrendStats: ["min", "avg", "med", "p(90)", "p(95)", "max"],
};

// Línea base de red: /health no consulta fuentes externas ni cuenta en el límite de tasa.
export function setup() {
  for (let i = 0; i < 5; i += 1) {
    redMs.add(http.get(`${BASE_URL}/health`).timings.duration);
  }
}

export default function () {
  const query = MODO === "misma" ? "Minecraft" : TITULOS[__VU - 1];

  const response = http.get(
    `${BASE_URL}/games/search?q=${encodeURIComponent(query)}`,
    { timeout: "60s" },
  );

  busquedaMs.add(response.timings.duration);

  const ok = check(response, {
    "respuesta HTTP 200": (result) => result.status === 200,
  });

  if (!ok) {
    (response.status === 429 ? estados429 : estadosOtros).add(1);
    return;
  }

  estadosOk.add(1);

  const games = response.json();

  if (games.length === 0) {
    vacias.add(1);
    return;
  }

  // Una respuesta cuenta una sola vez por fuente, aunque varios juegos lo avisen.
  const faltantes = new Set(
    games.flatMap((game) => game.unavailable_sources || []),
  );

  if (faltantes.has("Steam")) sinSteam.add(1);
  if (faltantes.has("CheapShark")) sinCheapShark.add(1);
  if (faltantes.has("PlayStation")) sinPlayStation.add(1);
}

function contador(data, nombre) {
  const metrica = data.metrics[nombre];
  return metrica ? metrica.values.count : 0;
}

export function handleSummary(data) {
  const duracion = data.metrics.busqueda_ms.values;
  const red = data.metrics.red_health_ms.values;

  const resumen = {
    modo: MODO,
    base_url: BASE_URL,
    fin_utc: new Date().toISOString(),
    solicitudes:
      contador(data, "estado_200") +
      contador(data, "estado_429") +
      contador(data, "estado_otro"),
    estado_200: contador(data, "estado_200"),
    estado_429: contador(data, "estado_429"),
    estado_otro: contador(data, "estado_otro"),
    respuestas_vacias: contador(data, "respuestas_vacias"),
    sin_steam: contador(data, "sin_steam"),
    sin_cheapshark: contador(data, "sin_cheapshark"),
    sin_playstation: contador(data, "sin_playstation"),
    min_ms: duracion.min,
    p50_ms: duracion.med,
    p90_ms: duracion["p(90)"],
    p95_ms: duracion["p(95)"],
    max_ms: duracion.max,
    red_health_p50_ms: red.med,
    duracion_corrida_ms: data.state.testRunDurationMs,
    umbral_p95_ms: 3000,
    cumple_umbral: duracion["p(95)"] <= 3000,
  };

  const linea =
    `modo=${MODO} 200=${resumen.estado_200} 429=${resumen.estado_429} ` +
    `otros=${resumen.estado_otro} vacias=${resumen.respuestas_vacias} ` +
    `p50=${resumen.p50_ms.toFixed(0)}ms p95=${resumen.p95_ms.toFixed(0)}ms ` +
    `max=${resumen.max_ms.toFixed(0)}ms sin_steam=${resumen.sin_steam} ` +
    `sin_cheapshark=${resumen.sin_cheapshark} sin_playstation=${resumen.sin_playstation} ` +
    `red_p50=${resumen.red_health_p50_ms.toFixed(0)}ms\n`;

  return {
    [SALIDA]: JSON.stringify(resumen, null, 2) + "\n",
    stdout: linea,
  };
}
