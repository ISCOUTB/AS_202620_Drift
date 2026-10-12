import { createPcProfile } from "../../domain/model/PcProfile";

export async function estimateCompatibility(
  gameId,
  specs,
  compatibilityRepository,
) {
  // Valida y normaliza el equipo antes de salir a la red.
  const profile = createPcProfile(specs);

  return compatibilityRepository.estimate(gameId, profile);
}
