const API_URL = process.env.NEXT_PUBLIC_DRIFT_API_URL || "http://localhost:8000";

/** Adaptador de `GET /games/explore`. */
export const fastApiExploreRepository = {
  async explore({ genre = null, tags = [], sort, price, page = 1 }) {
    const params = new URLSearchParams();

    if (genre) {
      params.set("genre", genre);
    }

    for (const tag of tags) {
      params.append("tag", tag);
    }

    if (sort) {
      params.set("sort", sort);
    }

    if (price) {
      params.set("price", price);
    }

    params.set("page", String(page));

    const response = await fetch(`${API_URL}/games/explore?${params}`);

    if (!response.ok) {
      const error = new Error("No se pudo cargar el catálogo.");
      error.status = response.status;
      throw error;
    }

    return response.json();
  },
};
