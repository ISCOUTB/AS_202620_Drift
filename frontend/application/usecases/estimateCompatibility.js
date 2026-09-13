export async function estimateCompatibility(
  gameId,
  { ramGb, gpuScore },
  compatibilityRepository,
) {
  const normalizedRamGb = Number(ramGb);
  const normalizedGpuScore = Number(gpuScore);

  if (!Number.isFinite(normalizedRamGb) || normalizedRamGb <= 0) {
    throw new Error("Ingresa una cantidad válida de RAM.");
  }

  if (!Number.isFinite(normalizedGpuScore) || normalizedGpuScore <= 0) {
    throw new Error("Ingresa un nivel válido de GPU.");
  }

  return compatibilityRepository.estimate(gameId, {
    ramGb: normalizedRamGb,
    gpuScore: normalizedGpuScore,
  });
}