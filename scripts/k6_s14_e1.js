// Medición S14 del escenario E1: rendimiento de la búsqueda.
//
// E1 (arc42 §10.2): con hasta 50 usuarios concurrentes en operación normal,
// la búsqueda responde en ≤ 3 s en el percentil 95.
//
// 50 usuarios virtuales hacen ITERACIONES búsquedas cada uno, todas con un
// texto distinto, así que ninguna aprovecha la caché de otra (caché fría).
//
// En local (lo lanza scripts/s14_corrida.py):
//   k6 run -e BASE_URL=http://127.0.0.1:8200 -e SALIDA=out.json scripts/k6_s14_e1.js
//
// Contra el entorno desplegado (la ruta de búsqueda cambia según el backend):
//   k6 run -e BASE_URL=https://<host> -e RUTA=/games/search -e SALIDA=out.json scripts/k6_s14_e1.js
//
// El umbral se fija aquí, antes de ejecutar, y es el declarado en arc42 §10.

import http from "k6/http";
import { check } from "k6";

const BASE_URL = __ENV.BASE_URL || "http://127.0.0.1:8200";
const RUTA = __ENV.RUTA || "/games/search";
const SALIDA = __ENV.SALIDA || "s14-e1-resultado.json";
const ITERACIONES = Number(__ENV.ITERACIONES || 4);
const PREFIJO = __ENV.PREFIJO || "s14 juego";

export const options = {
  scenarios: {
    e1_busqueda: {
      executor: "per-vu-iterations",
      vus: 50,
      iterations: ITERACIONES,
      maxDuration: "300s",
    },
  },
  thresholds: {
    http_req_duration: ["p(95)<=3000"],
    http_req_failed: ["rate<0.01"],
  },
  summaryTrendStats: ["min", "avg", "med", "p(90)", "p(95)", "max"],
};

export default function () {
  // Consulta distinta por usuario e iteración: "s14 juego 0107" es el
  // usuario 01 en su iteración 07.
  const numero = `${String(__VU).padStart(2, "0")}${String(__ITER).padStart(2, "0")}`;
  const query = `${PREFIJO} ${numero}`;

  const response = http.get(
    `${BASE_URL}${RUTA}?q=${encodeURIComponent(query)}`,
    { timeout: "60s" },
  );

  check(response, {
    "respuesta HTTP 200": (result) => result.status === 200,
    "devuelve juegos": (result) =>
      result.status === 200 && Array.isArray(result.json()) && result.json().length > 0,
  });
}

export function handleSummary(data) {
  const duracion = data.metrics.http_req_duration.values;
  const solicitudes = data.metrics.http_reqs.values.count;
  const fallidas = Math.round(data.metrics.http_req_failed.values.rate * solicitudes);
  const checks = data.metrics.checks.values;

  const resumen = {
    escenario: "E1",
    umbral_p95_ms: 3000,
    base_url: BASE_URL,
    usuarios_virtuales: 50,
    iteraciones_por_usuario: ITERACIONES,
    solicitudes: solicitudes,
    fallidas: fallidas,
    checks_superados: checks.passes,
    checks_fallidos: checks.fails,
    p50_ms: duracion.med,
    p90_ms: duracion["p(90)"],
    p95_ms: duracion["p(95)"],
    max_ms: duracion.max,
    cumple_p95: duracion["p(95)"] <= 3000,
    duracion_corrida_ms: data.state.testRunDurationMs,
  };

  const linea =
    `solicitudes=${resumen.solicitudes} fallidas=${resumen.fallidas} ` +
    `p50=${resumen.p50_ms.toFixed(0)}ms p95=${resumen.p95_ms.toFixed(0)}ms ` +
    `max=${resumen.max_ms.toFixed(0)}ms cumple=${resumen.cumple_p95}\n`;

  return {
    [SALIDA]: JSON.stringify(resumen, null, 2) + "\n",
    stdout: linea,
  };
}
