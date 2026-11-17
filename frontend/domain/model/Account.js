/** Cuenta y dispositivos del usuario, libres de dependencias de interfaz o red. */

import { createPcProfile } from "./PcProfile";

export const DEVICE_KINDS = {
  pc: { label: "PC", platform: "PC" },
  playstation: { label: "PlayStation", platform: "PlayStation" },
  xbox: { label: "Xbox", platform: "Xbox" },
};

export const MAX_DEVICE_NAME_LENGTH = 40;

export function createAccount({
  login_available = false,
  authenticated = false,
  user = null,
} = {}) {
  return {
    loginAvailable: Boolean(login_available),
    authenticated: Boolean(authenticated),
    user: user
      ? {
          name: String(user.name ?? ""),
          email: String(user.email ?? ""),
          picture: user.picture ?? null,
        }
      : null,
  };
}

/** Cuenta de quien no ha iniciado sesión o no puede hacerlo. */
export const ANONYMOUS_ACCOUNT = createAccount();

export function createDevice({ id, name, kind, specs = null }) {
  return {
    id: String(id),
    name: String(name),
    kind,
    specs,
  };
}

/** Iniciales para el avatar: «Ana María Ruiz» → «AM». */
export function initialsOf(name) {
  const words = String(name ?? "")
    .trim()
    .split(/\s+/)
    .filter(Boolean);

  return (
    words
      .slice(0, 2)
      .map((word) => word[0].toUpperCase())
      .join("") || "?"
  );
}

/** Plataformas que el usuario tiene, según sus dispositivos. */
export function platformsOfDevices(devices) {
  const owned = new Set(
    devices.map((device) => DEVICE_KINDS[device.kind]?.platform),
  );

  return ["PC", "PlayStation", "Xbox"].filter((platform) =>
    owned.has(platform),
  );
}

/** El equipo de un PC guardado, en la forma que usa la compatibilidad. */
export function pcProfileOfDevice(device) {
  if (device?.kind !== "pc" || !device.specs) {
    return null;
  }

  return createPcProfile({
    ramGb: device.specs.ram_gb,
    gpuName: device.specs.gpu_name,
    gpuScore: device.specs.gpu_score,
    cpuName: device.specs.cpu_name,
    cpuScore: device.specs.cpu_score,
    storageGb: device.specs.storage_gb,
  });
}

/** El equipo del navegador, en la forma que guarda el servidor. */
export function specsOfPcProfile(profile) {
  const specs = {
    ram_gb: profile.ramGb,
    gpu_score: profile.gpuScore,
  };

  if (profile.gpuName) {
    specs.gpu_name = profile.gpuName;
  }

  if (profile.cpuName) {
    specs.cpu_name = profile.cpuName;
    specs.cpu_score = profile.cpuScore;
  }

  if (profile.storageGb) {
    specs.storage_gb = profile.storageGb;
  }

  return specs;
}

/** «16 GB · RTX 3060 · Ryzen 5 5600». */
export function describeDevice(device) {
  if (device.kind !== "pc" || !device.specs) {
    return DEVICE_KINDS[device.kind]?.label ?? "";
  }

  return [
    `${device.specs.ram_gb} GB`,
    device.specs.gpu_name,
    device.specs.cpu_name,
  ]
    .filter(Boolean)
    .join(" · ");
}

export function validateDeviceName(name) {
  const clean = String(name ?? "").trim();

  if (!clean) {
    throw new Error("Ponle un nombre al dispositivo.");
  }

  if (clean.length > MAX_DEVICE_NAME_LENGTH) {
    throw new Error(
      `El nombre puede tener hasta ${MAX_DEVICE_NAME_LENGTH} caracteres.`,
    );
  }

  return clean;
}
