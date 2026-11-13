import {
  ANONYMOUS_ACCOUNT,
  createAccount,
  createDevice,
  specsOfPcProfile,
  validateDeviceName,
} from "../../domain/model/Account";
import {
  createFavorite,
  createFavoriteAlerts,
  favoriteOfGame,
  parseTargetPrice,
} from "../../domain/model/Favorite";

/** Quién está usando DRIFT. Si la API no responde, se sigue sin sesión. */
export async function loadAccount(accountRepository) {
  try {
    return createAccount(await accountRepository.current());
  } catch {
    return ANONYMOUS_ACCOUNT;
  }
}

export async function listDevices(accountRepository) {
  return (await accountRepository.listDevices()).map(createDevice);
}

export async function addConsole(kind, name, accountRepository) {
  return createDevice(
    await accountRepository.addDevice({
      name: validateDeviceName(name),
      kind,
    }),
  );
}

/** Guarda en la cuenta el equipo que el usuario tenía en su navegador. */
export async function addPc(name, pcProfile, accountRepository) {
  return createDevice(
    await accountRepository.addDevice({
      name: validateDeviceName(name),
      kind: "pc",
      specs: specsOfPcProfile(pcProfile),
    }),
  );
}

export function removeDevice(deviceId, accountRepository) {
  return accountRepository.removeDevice(deviceId);
}

export function logout(accountRepository) {
  return accountRepository.logout();
}

export function deleteAccount(accountRepository) {
  return accountRepository.deleteAccount();
}

export async function listFavorites(accountRepository) {
  return (await accountRepository.listFavorites()).map(createFavorite);
}

/** Guarda el juego con su mejor precio de ahora como referencia. */
export async function saveFavorite(game, accountRepository) {
  return createFavorite(
    await accountRepository.saveFavorite(game.id, favoriteOfGame(game)),
  );
}

export function removeFavorite(gameId, accountRepository) {
  return accountRepository.removeFavorite(gameId);
}

/** Pone el precio objetivo escrito por la persona; vacío lo quita. */
export async function setFavoriteTarget(gameId, text, accountRepository) {
  const target = String(text ?? "").trim() ? parseTargetPrice(text) : null;

  return createFavorite(
    await accountRepository.setFavoriteTarget(gameId, target),
  );
}

/** Precio de hoy de los favoritos y cuáles avisan (ADR-0021). */
export async function checkFavoriteAlerts(accountRepository) {
  return createFavoriteAlerts(await accountRepository.favoriteAlerts());
}
