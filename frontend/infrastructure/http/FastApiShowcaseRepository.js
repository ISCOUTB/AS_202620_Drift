const API_URL = process.env.NEXT_PUBLIC_DRIFT_API_URL || "http://localhost:8000";

async function getJson(path) {
  const response = await fetch(`${API_URL}${path}`);

  if (!response.ok) {
    throw new Error("No se pudo consultar la portada.");
  }

  return response.json();
}

/** Adaptador de lo que muestra la portada: juegos del momento y tiendas. */
export const fastApiShowcaseRepository = {
  async featured(category) {
    const query = category
      ? `?category=${encodeURIComponent(category)}`
      : "";

    return (await getJson(`/games/featured${query}`)).items;
  },

  stores() {
    return getJson("/stores");
  },
};
