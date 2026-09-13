import http from "k6/http";
import { check } from "k6";

export const options = {
  scenarios: {
    baseline_search: {
      executor: "per-vu-iterations",
      vus: 50,
      iterations: 1,
      maxDuration: "30s",
    },
  },
  thresholds: {
    http_req_duration: ["p(95)<3000"],
    http_req_failed: ["rate<0.01"],
  },
  summaryTrendStats: ["min", "avg", "med", "p(90)", "p(95)", "max"],
};

export default function () {
  const response = http.get(
    "http://127.0.0.1:8000/games/search?q=Minecraft",
  );

  check(response, {
    "respuesta HTTP 200": (result) => result.status === 200,
  });
}