import { defineGameDetailsPort } from "../../application/ports/GameDetailsPort";
import { createGameDetails } from "../../domain/model/GameDetails";

const API_URL = process.env.NEXT_PUBLIC_DRIFT_API_URL || "http://localhost:8000";

/** Adaptador HTTP de la ficha de un juego (`GET /games/{id}/details`). */
export const fastApiGameDetailsRepository = defineGameDetailsPort({
  async get(gameId) {
    const response = await fetch(
      `${API_URL}/games/${encodeURIComponent(gameId)}/details`,
    );

    // Sin ficha de Steam: la página muestra solo los precios.
    if (response.status === 404) {
      return null;
    }

    if (!response.ok) {
      throw new Error("No pudimos cargar la ficha del juego.");
    }

    return createGameDetails(await response.json());
  },
});
