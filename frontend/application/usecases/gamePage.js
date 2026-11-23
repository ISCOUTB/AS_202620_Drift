import { findGameInResults, steamIdOf } from "../../domain/model/GameDetails";

/**
 * Ficha del juego para su página. `null` si no tiene (no es de Steam o
 * Steam no lo conoce). Rechaza solo si Steam no respondió.
 */
export async function getGameDetails(gameId, gameDetailsRepository) {
  const steamId = steamIdOf(gameId);

  if (!steamId) {
    return null;
  }

  return gameDetailsRepository.get(steamId);
}

/**
 * Precios del juego de la página. Primero los que dejó la búsqueda de la
 * que se viene (sin volver a consultar las tiendas); si no hay, se busca
 * por su nombre en todas las tiendas y se elige el mismo juego.
 */
export async function loadGamePrices(
  { gameId, name },
  { handoffRepository, gameRepository },
) {
  const handed = handoffRepository.take(gameId);

  if (handed) {
    return handed;
  }

  if (!name?.trim()) {
    return null;
  }

  // Algunas tiendas no encuentran el título completo («Juego - Edición»):
  // si no aparece, se intenta una vez con la parte antes del guion o los
  // dos puntos.
  for (const query of searchTermsFor(name)) {
    const found = findGameInResults(await gameRepository.search(query), gameId, name);

    if (found) {
      return found;
    }
  }

  return null;
}

export function searchTermsFor(name) {
  const full = name.trim();
  const short = full.split(/\s[-–—:]\s|:\s/)[0].trim();

  return short && short !== full && short.length >= 3 ? [full, short] : [full];
}
