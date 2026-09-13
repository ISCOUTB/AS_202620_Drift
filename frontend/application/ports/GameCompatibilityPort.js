export function defineGameCompatibilityPort(adapter) {
  if (!adapter || typeof adapter.estimate !== "function") {
    throw new Error("El adaptador debe implementar estimate(gameId, specs).");
  }

  return adapter;
}