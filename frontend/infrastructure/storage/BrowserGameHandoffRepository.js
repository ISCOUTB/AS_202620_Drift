/**
 * Juego que la búsqueda entrega a su página, en `sessionStorage`. Así la
 * página usa los precios que ya se mostraron y no vuelve a consultar las
 * tiendas. Vale unos minutos: después, la página los pide de nuevo.
 */

const PREFIX = "drift.game.";
const MAX_AGE_MS = 10 * 60 * 1000;

const keyOf = (gameId) => `${PREFIX}${String(gameId).replace(/^steam-/, "")}`;

export const browserGameHandoffRepository = {
  give(game) {
    try {
      globalThis.sessionStorage?.setItem(
        keyOf(game.id),
        JSON.stringify({ savedAt: Date.now(), game }),
      );
    } catch {
      // Sin almacenamiento la página buscará los precios por su cuenta.
    }
  },

  take(gameId) {
    try {
      const stored = globalThis.sessionStorage?.getItem(keyOf(gameId));

      if (!stored) {
        return null;
      }

      const { savedAt, game } = JSON.parse(stored);

      if (typeof savedAt !== "number" || Date.now() - savedAt > MAX_AGE_MS) {
        globalThis.sessionStorage?.removeItem(keyOf(gameId));
        return null;
      }

      return game && typeof game === "object" ? game : null;
    } catch {
      return null;
    }
  },
};
