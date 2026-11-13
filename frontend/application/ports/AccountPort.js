const REQUIRED = [
  "current",
  "loginUrl",
  "logout",
  "deleteAccount",
  "listDevices",
  "addDevice",
  "removeDevice",
  "listFavorites",
  "saveFavorite",
  "removeFavorite",
  "setFavoriteTarget",
  "favoriteAlerts",
];

export function defineAccountPort(adapter) {
  for (const method of REQUIRED) {
    if (!adapter || typeof adapter[method] !== "function") {
      throw new Error(`El adaptador de cuentas debe implementar ${method}().`);
    }
  }

  return adapter;
}
