import { findGpuScore } from "./GpuCatalog";

function isPositiveInteger(value) {
  return Number.isInteger(value) && value > 0;
}

function isBlank(value) {
  return value === null || value === undefined || value === "";
}

/** Equipo del usuario, libre de dependencias de interfaz o red. */
export function createPcProfile({
  ramGb,
  gpuName,
  gpuScore,
  cpuName,
  cpuScore,
  storageGb,
}) {
  const normalizedRamGb = Number(ramGb);

  if (!isPositiveInteger(normalizedRamGb)) {
    throw new Error("Ingresa una cantidad válida de RAM.");
  }

  const normalizedGpuScore = Number(gpuScore ?? findGpuScore(gpuName));

  if (!isPositiveInteger(normalizedGpuScore)) {
    throw new Error("Elige tu tarjeta gráfica.");
  }

  // El procesador es opcional: sin él ese componente no se compara.
  const hasCpu = !isBlank(cpuName);
  const normalizedCpuScore = hasCpu ? Number(cpuScore) : null;

  if (hasCpu && !isPositiveInteger(normalizedCpuScore)) {
    throw new Error("Elige tu procesador de la lista.");
  }

  const hasStorage = !isBlank(storageGb);
  const normalizedStorageGb = hasStorage ? Number(storageGb) : null;

  if (hasStorage && !isPositiveInteger(normalizedStorageGb)) {
    throw new Error("Ingresa un espacio libre válido o deja el campo vacío.");
  }

  return {
    ramGb: normalizedRamGb,
    gpuName: gpuName ? String(gpuName) : null,
    gpuScore: normalizedGpuScore,
    cpuName: hasCpu ? String(cpuName) : null,
    cpuScore: normalizedCpuScore,
    storageGb: normalizedStorageGb,
  };
}
