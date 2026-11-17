/**
 * Página «Explorar»: géneros, filtros y la ficha de cada juego del catálogo.
 * Los identificadores son los mismos que acepta `GET /games/explore`.
 */

export const EXPLORE_GENRES = [
  { slug: "accion", name: "Acción" },
  { slug: "aventura", name: "Aventura" },
  { slug: "rol", name: "Rol" },
  { slug: "estrategia", name: "Estrategia" },
  { slug: "simulacion", name: "Simulación" },
  { slug: "deportes", name: "Deportes" },
  { slug: "carreras", name: "Carreras" },
  { slug: "terror", name: "Terror" },
  { slug: "casuales", name: "Casuales" },
];

export const EXPLORE_TAGS = [
  { slug: "un-jugador", name: "Un jugador" },
  { slug: "multijugador", name: "Multijugador" },
  { slug: "cooperativo", name: "Cooperativo" },
  { slug: "mundo-abierto", name: "Mundo abierto" },
  { slug: "buena-trama", name: "Buena trama" },
  { slug: "indie", name: "Indie" },
  { slug: "anime", name: "Anime" },
  { slug: "pixelados", name: "Pixelados" },
  { slug: "fantasia", name: "Fantasía" },
  { slug: "ciencia-ficcion", name: "Ciencia ficción" },
  { slug: "supervivencia", name: "Supervivencia" },
  { slug: "por-turnos", name: "Estrategia por turnos" },
];

export const EXPLORE_SORTS = [
  { slug: "populares", name: "Más vendidos" },
  { slug: "valorados", name: "Mejor valorados" },
  { slug: "precio-asc", name: "Precio: de menor a mayor" },
  { slug: "precio-desc", name: "Precio: de mayor a menor" },
];

export const EXPLORE_PRICES = [
  { slug: "todos", name: "Cualquier precio" },
  { slug: "gratis", name: "Gratis" },
  { slug: "hasta-40000", name: "Hasta $40.000" },
  { slug: "hasta-100000", name: "Hasta $100.000" },
  { slug: "ofertas", name: "En oferta" },
];

export const DEFAULT_FILTERS = Object.freeze({
  tags: [],
  sort: "populares",
  price: "todos",
});

export const MAX_EXPLORE_PAGE = 20;
export const MAX_SELECTED_TAGS = 6;

const bySlug = (list) => Object.fromEntries(list.map((item) => [item.slug, item]));

const GENRES = bySlug(EXPLORE_GENRES);
const TAGS = bySlug(EXPLORE_TAGS);
const SORTS = bySlug(EXPLORE_SORTS);
const PRICES = bySlug(EXPLORE_PRICES);

export function findGenre(slug) {
  return GENRES[slug] ?? null;
}

export function tagName(slug) {
  return TAGS[slug]?.name ?? slug;
}

/** Un parámetro de la dirección que puede venir una vez, varias o ninguna. */
function asList(value) {
  if (Array.isArray(value)) {
    return value;
  }

  return value ? [value] : [];
}

/** Filtros leídos de la dirección; lo desconocido se descarta. */
export function filtersFromParams(params = {}) {
  const tags = asList(params.etiqueta)
    .filter((slug) => TAGS[slug])
    .slice(0, MAX_SELECTED_TAGS);

  return {
    tags: [...new Set(tags)],
    sort: SORTS[params.orden] ? params.orden : DEFAULT_FILTERS.sort,
    price: PRICES[params.precio] ? params.precio : DEFAULT_FILTERS.price,
  };
}

/** Parte de la dirección que guarda los filtros, para poder compartirla. */
export function filtersToSearch(filters) {
  const params = new URLSearchParams();

  for (const tag of filters.tags) {
    params.append("etiqueta", tag);
  }

  if (filters.sort !== DEFAULT_FILTERS.sort) {
    params.set("orden", filters.sort);
  }

  if (filters.price !== DEFAULT_FILTERS.price) {
    params.set("precio", filters.price);
  }

  const text = params.toString();

  return text ? `?${text}` : "";
}

/** Chips de los filtros activos, con lo que hace falta para quitarlos. */
export function activeFilterChips(filters) {
  const chips = filters.tags.map((slug) => ({
    key: `tag-${slug}`,
    label: tagName(slug),
    remove: (current) => ({
      ...current,
      tags: current.tags.filter((tag) => tag !== slug),
    }),
  }));

  if (filters.price !== DEFAULT_FILTERS.price) {
    chips.push({
      key: "price",
      label: PRICES[filters.price].name,
      remove: (current) => ({ ...current, price: DEFAULT_FILTERS.price }),
    });
  }

  if (filters.sort !== DEFAULT_FILTERS.sort) {
    chips.push({
      key: "sort",
      label: SORTS[filters.sort].name,
      remove: (current) => ({ ...current, sort: DEFAULT_FILTERS.sort }),
    });
  }

  return chips;
}

export function createExploreGame(game) {
  const number = (value) =>
    value === null || value === undefined || Number.isNaN(Number(value))
      ? null
      : Number(value);

  return {
    id: String(game.id),
    name: String(game.name),
    image: game.image ?? null,
    hero: game.hero ?? null,
    header: game.header ?? null,
    capsule: game.capsule ?? null,
    description: game.description ?? null,
    tags: Array.isArray(game.tags) ? game.tags.map(String) : [],
    releaseDate: game.release_date ? new Date(`${game.release_date}T12:00:00Z`) : null,
    developers: Array.isArray(game.developers) ? game.developers.map(String) : [],
    review: game.review ?? null,
    reviewPercent: number(game.review_percent),
    price: number(game.price),
    originalPrice: number(game.original_price),
    discount: Number(game.discount) || 0,
    isFree: game.is_free === true,
  };
}

export function formatReleaseDate(date) {
  if (!date) {
    return null;
  }

  return date.toLocaleDateString("es-CO", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  });
}

function pesos(value) {
  return `$${value.toLocaleString("es-CO", { maximumFractionDigits: 0 })}`;
}

/** Precio en Steam tal como se muestra: gratis, con descuento o normal. */
export function describeSteamPrice(game) {
  if (game.isFree || game.price === 0) {
    return { text: "Gratis", original: null, discount: 0 };
  }

  if (game.price === null) {
    return { text: "Sin precio en Steam", original: null, discount: 0 };
  }

  return {
    text: pesos(game.price),
    original: game.originalPrice ? pesos(game.originalPrice) : null,
    discount: game.discount,
  };
}

/** Tono de la reseña, como en la tienda: positiva, mixta o negativa. */
export function reviewTone(game) {
  if (game.reviewPercent === null) {
    return "neutral";
  }

  if (game.reviewPercent >= 70) {
    return "positive";
  }

  return game.reviewPercent >= 40 ? "mixed" : "negative";
}

/** Imagen vertical; si no hay, la horizontal; si no, ninguna. */
export function posterOf(game) {
  return game.image || game.capsule || game.header || null;
}
