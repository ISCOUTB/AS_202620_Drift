import { FALLBACK_STORES, createStore } from "../../domain/model/Store";

/**
 * Juegos del momento para la portada. Nunca rechaza: si la API no responde
 * devuelve una lista vacía y la portada usa su lista incluida.
 */
export async function getFeaturedGames(category, showcaseRepository) {
  try {
    const items = await showcaseRepository.featured(category);

    return items.map((game) => ({
      // El prefijo evita chocar con los identificadores de la lista incluida.
      id: `steam-${game.id}`,
      name: String(game.name),
      genre: category ?? "Entre los más vendidos",
      image: game.image,
      hero: game.hero,
      header: game.header,
    }));
  } catch {
    return [];
  }
}

/** Tiendas conectadas. Nunca rechaza: sin API muestra las principales. */
export async function getStores(showcaseRepository) {
  try {
    const answer = await showcaseRepository.stores();
    const stores = answer.items.map(createStore);

    return stores.length > 0
      ? { complete: Boolean(answer.complete), stores }
      : { complete: false, stores: FALLBACK_STORES };
  } catch {
    return { complete: false, stores: FALLBACK_STORES };
  }
}
