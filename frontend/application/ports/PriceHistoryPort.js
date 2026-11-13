export function definePriceHistoryPort(adapter) {
  if (!adapter || typeof adapter.find !== "function") {
    throw new Error("El adaptador debe implementar find(gameId).");
  }

  return adapter;
}
