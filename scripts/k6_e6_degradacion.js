// Experimento E6: degradación de una fuente bajo carga.
//
// 50 usuarios virtuales, una búsqueda distinta cada uno y caché fría.
// El upstream simulado (scripts/stub_upstream.py) hace que CheapShark tarde
// más de 5 s en 18 de las 50 consultas.
//
//   k6 run -e SALIDA=docs/evidencias/e6-resultados/antes-1.json scripts/k6_e6_degradacion.js

import http from "k6/http";
import { check } from "k6";
import { Counter } from "k6/metrics";

const BASE_URL = __ENV.BASE_URL || "http://127.0.0.1:8100";
const SALIDA = __ENV.SALIDA || "e6-resultado.json";

const degradadas = new Counter("degradadas");
const degradadasSinAviso = new Counter("degradadas_sin_aviso");

export const options = {
  scenarios: {
    e6_degradacion: {
      executor: "per-vu-iterations",
      vus: 50,
      iterations: 1,
      maxDuration: "300s",
    },
  },
  thresholds: {
    http_req_duration: ["p(95)<=5000"],
    http_req_failed: ["rate<0.01"],
    degradadas_sin_aviso: ["count==0"],
  },
  summaryTrendStats: ["min", "avg", "med", "p(90)", "p(95)", "max"],
};

export default function () {
  // Una consulta distinta por usuario virtual: ninguna aprovecha la caché.
  const query = `e6 juego ${String(__VU).padStart(2, "0")}`;

  const response = http.get(
    `${BASE_URL}/games/search?q=${encodeURIComponent(query)}`,
    { timeout: "240s" },
  );

  const ok = check(response, {
    "respuesta HTTP 200": (result) => result.status === 200,
  });

  if (!ok) {
    return;
  }

  const games = response.json();

  // El upstream simulado siempre ofrece GOG a través de CheapShark: si no
  // aparece, la respuesta llegó sin esa fuente.
  const tieneCheapShark = games.some((game) => "GOG" in game.prices);

  if (tieneCheapShark) {
    return;
  }

  degradadas.add(1);

  const avisa =
    games.length > 0 &&
    games.every((game) =>
      (game.unavailable_sources || []).includes("CheapShark"),
    );

  if (!avisa) {
    degradadasSinAviso.add(1);
  }
}

function contador(data, nombre) {
  const metrica = data.metrics[nombre];
  return metrica ? metrica.values.count : 0;
}

export function handleSummary(data) {
  const duracion = data.metrics.http_req_duration.values;
  const solicitudes = contador(data, "http_reqs");
  const fallidas = Math.round(
    data.metrics.http_req_failed.values.rate * solicitudes,
  );

  const resumen = {
    solicitudes: solicitudes,
    fallidas: fallidas,
    p50_ms: duracion.med,
    p95_ms: duracion["p(95)"],
    max_ms: duracion.max,
    degradadas: contador(data, "degradadas"),
    degradadas_sin_aviso: contador(data, "degradadas_sin_aviso"),
    duracion_corrida_ms: data.state.testRunDurationMs,
  };

  const linea =
    `solicitudes=${resumen.solicitudes} fallidas=${resumen.fallidas} ` +
    `p50=${resumen.p50_ms.toFixed(0)}ms p95=${resumen.p95_ms.toFixed(0)}ms ` +
    `max=${resumen.max_ms.toFixed(0)}ms degradadas=${resumen.degradadas} ` +
    `sin_aviso=${resumen.degradadas_sin_aviso}\n`;

  return {
    [SALIDA]: JSON.stringify(resumen, null, 2) + "\n",
    stdout: linea,
  };
}
