/** Puerto de salida: la ficha de un juego (sinopsis, tráilers, capturas). */
export function defineGameDetailsPort(adapter) {
  if (!adapter || typeof adapter.get !== "function") {
    throw new Error("El adaptador debe implementar get(gameId).");
  }

  return adapter;
}
