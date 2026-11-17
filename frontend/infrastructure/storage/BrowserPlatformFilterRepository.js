import { PLATFORMS } from "../../domain/model/Game";

const STORAGE_KEY = "drift.platformFilter";

/** Adaptador que recuerda en el navegador las plataformas que tiene el usuario. */
export const browserPlatformFilterRepository = {
  load() {
    try {
      const stored = JSON.parse(
        globalThis.localStorage?.getItem(STORAGE_KEY) ?? "[]",
      );

      return Array.isArray(stored)
        ? PLATFORMS.filter((platform) => stored.includes(platform))
        : [];
    } catch {
      // Almacenamiento bloqueado o dato corrupto: se muestran todas.
      return [];
    }
  },

  save(platforms) {
    try {
      globalThis.localStorage?.setItem(STORAGE_KEY, JSON.stringify(platforms));
    } catch {
      // Sin almacenamiento el filtro vale solo para esta visita.
    }
  },
};
