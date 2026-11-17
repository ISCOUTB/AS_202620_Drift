/** Entidad del dominio, libre de dependencias de interfaz o red. */
export function createGame({
  id,
  name,
  prices = {},
  unavailable_sources = [],
  cached_sources = {},
  image = null,
  links = {},
  discounts = {},
  platforms,
}) {
  return {
    id: String(id),
    name: String(name),
    prices,
    unavailableSources: unavailable_sources,
    cachedSources: cached_sources || {},
    image,
    links,
    discounts: discounts || {},
    platforms: platforms ?? platformsOfStores(Object.keys(prices)),
  };
}

/** Plataformas que el usuario puede elegir en el filtro. */
export const PLATFORMS = ["PC", "PlayStation", "Xbox"];

/**
 * Plataforma para la que vende cada tienda: PlayStation Store y la tienda
 * de Xbox venden para su consola; todas las demás, para PC.
 */
export function platformOfStore(store) {
  if (store === "PlayStation" || store === "Xbox") {
    return store;
  }

  return "PC";
}

function platformsOfStores(stores) {
  const found = new Set(stores.map(platformOfStore));

  return PLATFORMS.filter((platform) => found.has(platform));
}

function keepStores(byStore, wanted) {
  return Object.fromEntries(
    Object.entries(byStore ?? {}).filter(([store]) =>
      wanted.has(platformOfStore(store)),
    ),
  );
}

/**
 * Deja en cada juego solo las tiendas de las plataformas elegidas y quita
 * los juegos que no se venden en ninguna. Sin plataformas elegidas no
 * filtra nada.
 */
export function filterByPlatforms(games, platforms) {
  if (!platforms?.length) {
    return games;
  }

  const wanted = new Set(platforms);

  return games
    .map((game) => {
      const prices = keepStores(game.prices, wanted);

      return {
        ...game,
        prices,
        links: keepStores(game.links, wanted),
        discounts: keepStores(game.discounts, wanted),
        platforms: platformsOfStores(Object.keys(prices)),
      };
    })
    .filter((game) => Object.keys(game.prices).length > 0);
}

/**
 * La compatibilidad se calcula con los requisitos de PC que publica Steam:
 * solo aplica a un juego con identificador de Steam (numérico) que se
 * venda para PC, o que no tenga precio en ninguna tienda (gratuito).
 */
export function canEstimatePcCompatibility(game) {
  if (!game || !/^\d+$/.test(game.id)) {
    return false;
  }

  return game.platforms.length === 0 || game.platforms.includes("PC");
}

/** Fuentes que agrupan a las demás tiendas de PC; el servidor usa una u otra. */
const PC_STORE_SOURCES = ["IsThereAnyDeal", "CheapShark"];

/**
 * Fuentes de las que puede salir el precio de una tienda. Steam,
 * PlayStation y Xbox se consultan directamente; las demás tiendas de PC
 * llegan por IsThereAnyDeal o, sin su llave, por CheapShark.
 */
function sourcesOfStore(store) {
  if (store === "Steam" || store === "PlayStation") {
    return [store];
  }

  if (store === "Xbox" || store === "Microsoft Store") {
    return ["Xbox"];
  }

  return PC_STORE_SOURCES;
}

/**
 * Fecha en que se obtuvo el precio de una tienda cuando su fuente no
 * respondió y se muestra la copia guardada; `null` si el precio es actual.
 */
export function cachedAtForStore(game, store) {
  const source = sourcesOfStore(store).find(
    (name) => game?.cachedSources?.[name],
  );

  return source ? game.cachedSources[source] : null;
}

/** «hace 2 h», «hace 35 min», «hace 3 días». */
export function describeAge(isoDate, now = Date.now()) {
  const capturedAt = Date.parse(isoDate);

  if (Number.isNaN(capturedAt)) {
    return "hace un tiempo";
  }

  const minutes = Math.max(1, Math.round((now - capturedAt) / 60000));

  if (minutes < 60) {
    return `hace ${minutes} min`;
  }

  const hours = Math.round(minutes / 60);

  if (hours < 24) {
    return `hace ${hours} h`;
  }

  const days = Math.round(hours / 24);

  return `hace ${days} ${days === 1 ? "día" : "días"}`;
}

/** Aviso de las fuentes que respondieron con su copia guardada. */
export function describeCachedSources(game, now = Date.now()) {
  return Object.entries(game?.cachedSources ?? {}).map(
    ([source, capturedAt]) => `${source} (${describeAge(capturedAt, now)})`,
  );
}
