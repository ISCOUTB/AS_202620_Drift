import { definePriceHistoryPort } from "../../application/ports/PriceHistoryPort";

const API_URL = process.env.NEXT_PUBLIC_DRIFT_API_URL || "http://localhost:8000";

export const fastApiPriceHistoryRepository = definePriceHistoryPort({
  async find(gameId) {
    const response = await fetch(
      `${API_URL}/games/${encodeURIComponent(gameId)}/price-history`,
    );

    if (!response.ok) {
      throw new Error("No se pudo consultar el historial de precios.");
    }

    return response.json();
  },
});
