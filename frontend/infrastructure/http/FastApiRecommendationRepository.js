import { defineRecommendationPort } from "../../application/ports/RecommendationPort";

const API_URL = process.env.NEXT_PUBLIC_DRIFT_API_URL || "http://localhost:8000";

export const fastApiRecommendationRepository = defineRecommendationPort({
  async recommend(gameId, prices, discounts, devices) {
    const response = await fetch(
      `${API_URL}/games/${encodeURIComponent(gameId)}/recommendation`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          prices,
          discounts: discounts ?? {},
          devices,
        }),
      },
    );

    if (!response.ok) {
      throw new Error("No se pudo calcular la recomendación.");
    }

    return response.json();
  },
});
