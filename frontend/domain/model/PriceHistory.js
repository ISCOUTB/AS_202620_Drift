/** Historial de precios de un juego, libre de dependencias de interfaz o red. */

function toPoint(point) {
  if (!point) {
    return null;
  }

  return {
    date: new Date(point.date),
    store: String(point.store),
    price: Number(point.price),
    discount: Number(point.discount) || 0,
  };
}

export function createPriceHistory({
  available = false,
  reason = null,
  since = null,
  cached_at = null,
  current = null,
  lowest = null,
  steam_best_discount = null,
  points = [],
}) {
  return {
    available: Boolean(available),
    reason,
    since: since ? new Date(since) : null,
    cachedAt: cached_at ? new Date(cached_at) : null,
    current: toPoint(current),
    lowest: toPoint(lowest),
    steamBestDiscount: steam_best_discount
      ? {
          date: new Date(steam_best_discount.date),
          discount: Number(steam_best_discount.discount) || 0,
        }
      : null,
    points: points.map(toPoint),
  };
}

/**
 * El historial sale de las tiendas de PC: solo aplica a un juego que se
 * venda para PC y que venga de Steam (identificador numérico) o de
 * IsThereAnyDeal (prefijo `itad-`).
 */
export function canHavePriceHistory(game) {
  if (!game?.platforms?.includes("PC")) {
    return false;
  }

  return /^\d+$/.test(game.id) || game.id.startsWith("itad-");
}
