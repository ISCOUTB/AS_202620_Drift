/** Puerto de salida: los casos de uso no conocen HTTP ni FastAPI. */
export function defineGameSearchPort(adapter) {
  if (!adapter || typeof adapter.search !== "function") {
    throw new Error("El adaptador debe implementar search(query).");
  }

  return adapter;
}
