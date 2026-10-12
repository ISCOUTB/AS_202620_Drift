import { definePcProfilePort } from "../../application/ports/PcProfilePort";
import { createPcProfile } from "../../domain/model/PcProfile";

const STORAGE_KEY = "drift.pcProfile";

/** Adaptador que guarda el equipo del usuario en su propio navegador. */
export const browserPcProfileRepository = definePcProfilePort({
  load() {
    try {
      const stored = globalThis.localStorage?.getItem(STORAGE_KEY);

      return stored ? createPcProfile(JSON.parse(stored)) : null;
    } catch {
      // Almacenamiento bloqueado o dato corrupto: se pide el equipo de nuevo.
      return null;
    }
  },

  save(profile) {
    try {
      globalThis.localStorage?.setItem(STORAGE_KEY, JSON.stringify(profile));
    } catch {
      // Sin almacenamiento el perfil vale solo para esta visita.
    }
  },
});
