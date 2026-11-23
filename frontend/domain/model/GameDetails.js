/**
 * Ficha de un juego para su página: sinopsis, tráilers, capturas y datos.
 * Solo los juegos de Steam la tienen; los demás muestran solo sus precios.
 */

const asList = (value) => (Array.isArray(value) ? value.map(String) : []);

export function createGameDetails({
  id,
  name,
  description = null,
  header_image = null,
  background_image = null,
  release_date = null,
  coming_soon = false,
  developers = [],
  publishers = [],
  genres = [],
  trailers = [],
  screenshots = [],
}) {
  return {
    id: String(id),
    name: String(name),
    description,
    headerImage: header_image,
    backgroundImage: background_image,
    releaseDate: release_date,
    comingSoon: Boolean(coming_soon),
    developers: asList(developers),
    publishers: asList(publishers),
    genres: asList(genres),
    trailers: (trailers ?? []).map((trailer) => ({
      name: String(trailer.name),
      thumbnail: trailer.thumbnail,
      hls: trailer.hls,
      dash: trailer.dash ?? null,
    })),
    screenshots: (screenshots ?? []).map((shot) => ({
      thumbnail: shot.thumbnail,
      full: shot.full,
    })),
  };
}

/** Identificador de Steam de un juego, sin el prefijo de la portada. */
export function steamIdOf(gameId) {
  const id = String(gameId ?? "").replace(/^steam-/, "");

  return /^\d{1,8}$/.test(id) ? id : null;
}

/** Solo un juego con identificador de Steam tiene ficha. */
export function hasGameDetails(gameId) {
  return steamIdOf(gameId) !== null;
}

/**
 * Dirección de la página de un juego. El nombre viaja en la dirección para
 * poder buscar sus precios aunque el juego no tenga ficha de Steam.
 */
export function gamePageUrl({ id, name }) {
  const gameId = steamIdOf(id) ?? String(id);
  const query = name ? `?nombre=${encodeURIComponent(name)}` : "";

  return `/juego/${encodeURIComponent(gameId)}${query}`;
}

/**
 * Medios de la página en el orden en que se muestran: primero los tráilers
 * y después las capturas.
 */
export function mediaOf(details) {
  if (!details) {
    return [];
  }

  return [
    ...details.trailers.map((trailer, index) => ({
      kind: "trailer",
      key: `trailer-${index}`,
      thumbnail: trailer.thumbnail,
      title: trailer.name,
      trailer,
    })),
    ...details.screenshots.map((shot, index) => ({
      kind: "screenshot",
      key: `screenshot-${index}`,
      thumbnail: shot.thumbnail,
      title: `Captura ${index + 1}`,
      full: shot.full,
    })),
  ];
}

function normalizedName(name) {
  return String(name ?? "")
    .normalize("NFKD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/[™®©]/g, " ")
    .toLocaleLowerCase("es")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

/**
 * El juego de la página dentro de los resultados de una búsqueda: por su
 * identificador y, si la búsqueda no lo trae con ese, por su nombre.
 */
export function findGameInResults(results, gameId, name) {
  const id = steamIdOf(gameId) ?? String(gameId);
  const byId = results.find((game) => game.id === id);

  if (byId) {
    return byId;
  }

  const wanted = normalizedName(name);

  return wanted
    ? results.find((game) => normalizedName(game.name) === wanted) ?? null
    : null;
}
