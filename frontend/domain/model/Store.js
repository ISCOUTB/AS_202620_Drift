/** Tiendas cuyos precios compara DRIFT, libres de dependencias de interfaz o red. */

// Página principal de cada tienda. Una tienda que no esté aquí se muestra
// sin enlace: es preferible a enviar a alguien a una dirección equivocada.
const STORE_SITES = {
  Steam: "https://store.steampowered.com/",
  PlayStation: "https://store.playstation.com/es-co/",
  Xbox: "https://www.xbox.com/es-CO/games/all-games",
  "Microsoft Store": "https://apps.microsoft.com/games",
  AllYouPlay: "https://www.allyouplay.com/",
  Blizzard: "https://shop.battle.net/",
  DLGamer: "https://www.dlgamer.com/",
  Dreamgame: "https://www.dreamgame.com/",
  DreamGame: "https://www.dreamgame.com/",
  "EA Store": "https://www.ea.com/",
  "Epic Game Store": "https://store.epicgames.com/",
  "Epic Games Store": "https://store.epicgames.com/",
  Fanatical: "https://www.fanatical.com/",
  FireFlower: "https://fireflowergames.com/",
  GameBillet: "https://www.gamebillet.com/",
  GamersGate: "https://www.gamersgate.com/",
  Gamesload: "https://www.gamesload.com/",
  Gamesporium: "https://gamesporium.com/",
  Gamesplanet: "https://us.gamesplanet.com/",
  "GamesPlanet DE": "https://de.gamesplanet.com/",
  "GamesPlanet FR": "https://fr.gamesplanet.com/",
  "GamesPlanet UK": "https://uk.gamesplanet.com/",
  "GamesPlanet US": "https://us.gamesplanet.com/",
  GOG: "https://www.gog.com/",
  GreenManGaming: "https://www.greenmangaming.com/",
  "Humble Store": "https://www.humblebundle.com/store",
  IndieGala: "https://www.indiegala.com/",
  "IndieGala Store": "https://www.indiegala.com/",
  JoyBuggy: "https://joybuggy.com/",
  MacGameStore: "https://www.macgamestore.com/",
  Muve: "https://muve.games/",
  Newegg: "https://www.newegg.com/",
  Nuuvem: "https://www.nuuvem.com/",
  PlanetPlay: "https://www.planetplay.com/",
  PlayerLand: "https://player.land/",
  Playsum: "https://www.playsum.live/",
  "Ubisoft Store": "https://store.ubisoft.com/",
  Uplay: "https://store.ubisoft.com/",
  WinGameStore: "https://www.wingamestore.com/",
  Zapagames: "https://zapagames.com/",
  "ZOOM Platform": "https://www.zoom-platform.com/",
};

const STORE_NOTES = {
  Steam: "Precio de Colombia, en pesos",
  Xbox: "Precio de Colombia, en pesos",
  "Microsoft Store": "Precio de Colombia, en pesos",
  PlayStation: "Tienda de Colombia; cobra en dólares",
};

const DEFAULT_NOTE = "Precio de Estados Unidos convertido a pesos";

export const STORE_PLATFORMS = ["PC", "PlayStation", "Xbox"];

export function createStore({ name, platform = "PC", source = null }) {
  const url = STORE_SITES[name] ?? null;

  return {
    name: String(name),
    platform,
    source,
    url,
    // El ícono es el de la propia tienda; si no carga se usan sus iniciales.
    logo: url ? `${new URL(url).origin}/favicon.ico` : null,
    note: STORE_NOTES[name] ?? DEFAULT_NOTE,
  };
}

/** Iniciales para cuando el ícono de la tienda no está disponible. */
export function storeInitials(name) {
  const words = String(name).split(/[\s-]+/).filter(Boolean);

  if (words.length === 1) {
    return words[0].slice(0, 2).toUpperCase();
  }

  return words
    .slice(0, 2)
    .map((word) => word[0].toUpperCase())
    .join("");
}

export function groupStoresByPlatform(stores) {
  return STORE_PLATFORMS.map((platform) => ({
    platform,
    stores: stores.filter((store) => store.platform === platform),
  })).filter((group) => group.stores.length > 0);
}

/** Tiendas que se muestran si la API no entrega la lista. */
export const FALLBACK_STORES = [
  { name: "Steam", platform: "PC" },
  { name: "Microsoft Store", platform: "PC" },
  { name: "GOG", platform: "PC" },
  { name: "Epic Game Store", platform: "PC" },
  { name: "Humble Store", platform: "PC" },
  { name: "Fanatical", platform: "PC" },
  { name: "PlayStation", platform: "PlayStation" },
  { name: "Xbox", platform: "Xbox" },
].map(createStore);
