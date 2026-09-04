export async function searchGames(query, gameRepository) {
  const normalizedQuery = query.trim();
  if (!normalizedQuery) throw new Error("Escribe el nombre de un videojuego.");
  return gameRepository.search(normalizedQuery);
}
