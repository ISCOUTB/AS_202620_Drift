/** Juegos favoritos del usuario, libres de dependencias de interfaz o red. */

export function createFavorite({
  game_id,
  name,
  image = null,
  price = null,
  store = null,
  saved_at = null,
  target_price = null,
}) {
  return {
    gameId: String(game_id),
    name: String(name),
    image: image ?? null,
    price: price === null || price === undefined ? null : Number(price),
    store: store ?? null,
    savedAt: saved_at ? new Date(saved_at) : null,
    targetPrice:
      target_price === null || target_price === undefined
        ? null
        : Number(target_price),
  };
}

/** Precio de hoy y alerta de cada favorito, por identificador del juego. */
export function createFavoriteAlerts({
  checked_at = null,
  alerts = 0,
  items = [],
} = {}) {
  return {
    checkedAt: checked_at ? new Date(checked_at) : null,
    count: Number(alerts) || 0,
    byGame: Object.fromEntries(
      items.map((item) => [
        String(item.game_id),
        {
          current: item.current
            ? {
                store: String(item.current.store),
                price: Number(item.current.price),
              }
            : null,
          alert: item.alert
            ? {
                reason: item.alert.reason,
                savedDifference:
                  item.alert.saved_difference === null ||
                  item.alert.saved_difference === undefined
                    ? null
                    : Number(item.alert.saved_difference),
              }
            : null,
        },
      ]),
    ),
  };
}

/** Lo que escribe la persona en «Avísame si baja de»: pesos enteros. */
export function parseTargetPrice(text) {
  const digits = String(text ?? "").replace(/[^\d]/g, "");

  if (!digits) {
    throw new Error("Escribe el precio al que quieres que te avisemos.");
  }

  const value = Number(digits);

  if (!Number.isSafeInteger(value) || value <= 0 || value > 1_000_000_000) {
    throw new Error("Escribe un precio mayor que cero.");
  }

  return value;
}

function bestOffer(prices = {}) {
  return Object.entries(prices).reduce(
    (best, [store, price]) =>
      best === null || Number(price) < best.price
        ? { store, price: Number(price) }
        : best,
    null,
  );
}

/** Lo que se guarda de un juego: su mejor precio de ahora es la referencia. */
export function favoriteOfGame(game) {
  const best = bestOffer(game.prices);

  const favorite = { name: game.name };

  // El servidor solo acepta imágenes por https.
  if (typeof game.image === "string" && game.image.startsWith("https://")) {
    favorite.image = game.image;
  }

  if (best) {
    favorite.price = best.price;
    favorite.store = best.store;
  }

  return favorite;
}

export function findFavorite(favorites, game) {
  return favorites.find((favorite) => favorite.gameId === game?.id) ?? null;
}

/**
 * Cómo cambió el mejor precio de un juego desde que se guardó.
 * `null` si no hay con qué comparar o si el cambio es menor a un peso.
 */
export function priceChangeSince(favorite, game) {
  const best = bestOffer(game?.prices);

  if (!favorite || favorite.price === null || !best) {
    return null;
  }

  const difference = best.price - favorite.price;

  if (Math.abs(difference) < 1) {
    return null;
  }

  return {
    direction: difference < 0 ? "down" : "up",
    amount: Math.abs(difference),
    store: best.store,
  };
}
