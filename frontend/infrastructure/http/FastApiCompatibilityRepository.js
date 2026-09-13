import { defineGameCompatibilityPort } from "../../application/ports/GameCompatibilityPort";

const API_URL = process.env.NEXT_PUBLIC_DRIFT_API_URL || "http://localhost:8000";

export const fastApiCompatibilityRepository = defineGameCompatibilityPort({
  async estimate(gameId, { ramGb, gpuScore }) {
    const response = await fetch(
      `${API_URL}/games/${encodeURIComponent(gameId)}/compatibility`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ram_gb: ramGb,
          gpu_score: gpuScore,
        }),
      },
    );

    if (!response.ok) {
      throw new Error("No se pudo estimar la compatibilidad.");
    }

    return response.json();
  },
});