/** Entidad del dominio, libre de dependencias de interfaz o red. */
export function createGame({
  id,
  name,
  prices = {},
  unavailable_sources = [],
}) {
  return {
    id: String(id),
    name: String(name),
    prices,
    unavailableSources: unavailable_sources,
  };
}