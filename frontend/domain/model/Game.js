/** Entidad del dominio, libre de dependencias de interfaz o red. */
export function createGame({ id, name, prices = {} }) {
  return { id: String(id), name: String(name), prices };
}
