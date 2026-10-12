export function defineHardwareCatalogPort(adapter) {
  if (!adapter || typeof adapter.list !== "function") {
    throw new Error("El adaptador debe implementar list().");
  }

  return adapter;
}
