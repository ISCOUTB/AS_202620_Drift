import { createExploreGame } from "../../domain/model/Explore";

/**
 * Una página del catálogo. Rechaza si la API no responde: la página decide
 * si muestra un aviso o deja lo que ya tenía.
 */
export async function exploreGames(query, exploreRepository) {
  const answer = await exploreRepository.explore(query);

  return {
    page: Number(answer.page) || query.page || 1,
    hasMore: Boolean(answer.has_more),
    items: (answer.items ?? []).map(createExploreGame),
  };
}

/** Una sección de la portada de «Explorar»: si falla, queda vacía. */
export async function exploreSection(query, exploreRepository) {
  try {
    return (await exploreGames(query, exploreRepository)).items;
  } catch {
    return [];
  }
}
