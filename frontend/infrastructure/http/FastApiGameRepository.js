import { createGame } from "../../domain/model/Game";
import { defineGameSearchPort } from "../../application/ports/GameSearchPort";

const API_URL = process.env.NEXT_PUBLIC_DRIFT_API_URL || "http://localhost:8000";

/** Adaptador HTTP que implementa el puerto de búsqueda de juegos. */
export const fastApiGameRepository = defineGameSearchPort({
  async search(query) {
    const response = await fetch(`${API_URL}/games/search?q=${encodeURIComponent(query)}`);
    if (!response.ok) throw new Error("No se pudo realizar la búsqueda.");
    return (await response.json()).map(createGame);
  },
});
