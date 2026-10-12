import { defineHardwareCatalogPort } from "../../application/ports/HardwareCatalogPort";

const API_URL = process.env.NEXT_PUBLIC_DRIFT_API_URL || "http://localhost:8000";

function createCatalogRepository(path, errorMessage) {
  return defineHardwareCatalogPort({
    async list() {
      const response = await fetch(`${API_URL}${path}`);

      if (!response.ok) {
        throw new Error(errorMessage);
      }

      const catalogue = await response.json();

      return catalogue.items.map((item) => ({
        name: item.name,
        score: item.level,
        laptop: item.laptop,
      }));
    },
  });
}

/** Adaptadores HTTP de los catálogos de «Mi PC» (sin puntajes de benchmark). */
export const fastApiGpuCatalogRepository = createCatalogRepository(
  "/hardware/gpus",
  "No se pudo cargar el catálogo de tarjetas gráficas.",
);

export const fastApiCpuCatalogRepository = createCatalogRepository(
  "/hardware/cpus",
  "No se pudo cargar el catálogo de procesadores.",
);
