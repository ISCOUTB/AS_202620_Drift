/** Recomendación de compra, libre de dependencias de interfaz o red. */

import { specsOfPcProfile } from "./Account";

function toOption(option) {
  if (!option) {
    return null;
  }

  return {
    store: String(option.store),
    platform: String(option.platform),
    price: Number(option.price),
    discount: Number(option.discount) || 0,
    experience: option.experience ?? null,
    device: option.device
      ? {
          id: String(option.device.id),
          name: String(option.device.name),
          kind: option.device.kind,
        }
      : null,
  };
}

export function createRecommendation({
  uses_devices = false,
  recommended = null,
  reason = null,
  price_difference = 0,
  alternatives = [],
  excluded = [],
} = {}) {
  return {
    usesDevices: Boolean(uses_devices),
    recommended: toOption(recommended),
    reason,
    priceDifference: Number(price_difference) || 0,
    alternatives: alternatives.map(toOption),
    excluded: excluded.map((item) => ({
      device: {
        id: String(item.device.id),
        name: String(item.device.name),
        kind: item.device.kind,
      },
      reason: item.reason,
    })),
  };
}

const CONSOLE_OF_PLATFORM = {
  PlayStation: { kind: "playstation", name: "Tu PlayStation" },
  Xbox: { kind: "xbox", name: "Tu Xbox" },
};

/**
 * Dispositivos con los que se pide la recomendación.
 *
 * Con sesión, los registrados en la cuenta. Sin sesión, lo que el navegador
 * sabe: el PC guardado y las consolas marcadas en el filtro «Tengo:».
 */
export function devicesForRecommendation({
  accountDevices = [],
  pcProfile = null,
  platformFilter = [],
}) {
  if (accountDevices.length > 0) {
    return accountDevices.map(({ id, name, kind, specs }) => ({
      id,
      name,
      kind,
      ...(kind === "pc" && specs ? { specs } : {}),
    }));
  }

  const devices = [];

  if (pcProfile) {
    devices.push({
      name: "Tu PC",
      kind: "pc",
      specs: specsOfPcProfile(pcProfile),
    });
  }

  platformFilter.forEach((platform) => {
    if (CONSOLE_OF_PLATFORM[platform]) {
      devices.push(CONSOLE_OF_PLATFORM[platform]);
    }
  });

  return devices;
}

/** Cambia cuando cambia algo de lo que depende la recomendación. */
export function recommendationKey(game, devices) {
  return JSON.stringify([game.id, game.prices, devices]);
}

const EXPERIENCE_TEXT = {
  recommended: "alcanza los requisitos recomendados",
  minimum: "alcanza solo los requisitos mínimos",
  console: "es la versión hecha para esa consola",
  unverified: "no pudimos comprobar los requisitos en ese PC",
};

export function describeExperience(experience) {
  return EXPERIENCE_TEXT[experience] ?? "";
}

/** Por qué esa opción quedó de primera, en una frase. */
export function describeReason(recommendation, formatPrice) {
  const { reason, priceDifference, recommended, usesDevices } = recommendation;

  if (reason === "better_experience") {
    return `Cuesta ${formatPrice(priceDifference)} más que la opción más barata, pero ahí se juega mejor.`;
  }

  if (reason === "only_option") {
    return usesDevices
      ? "Es la única opción que puedes jugar con tus dispositivos."
      : "Es la única tienda con precio en este momento.";
  }

  if (priceDifference > 0) {
    return usesDevices
      ? `Es la más barata entre tus dispositivos: ahorras ${formatPrice(priceDifference)} frente a la siguiente.`
      : `Es la más barata: ${formatPrice(priceDifference)} menos que en ${
          recommendation.alternatives[0]?.platform ?? "otra plataforma"
        }.`;
  }

  return recommended?.price === 0
    ? "Es gratis."
    : "Es el precio más bajo disponible.";
}

const EXCLUDED_TEXT = {
  insufficient: "no alcanza los requisitos mínimos",
  not_sold: "el juego no se vende para ese dispositivo",
};

export function describeExcluded(item) {
  return `${item.device.name}: ${EXCLUDED_TEXT[item.reason] ?? "no aplica"}`;
}
