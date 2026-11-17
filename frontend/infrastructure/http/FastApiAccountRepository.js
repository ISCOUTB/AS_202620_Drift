import { defineAccountPort } from "../../application/ports/AccountPort";

const API_URL = process.env.NEXT_PUBLIC_DRIFT_API_URL || "http://localhost:8000";

// La sesión viaja en una cookie que este código no puede leer: solo se le
// pide al navegador que la envíe.
async function call(path, { method = "GET", body } = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    method,
    credentials: "include",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    let message = "No pudimos completar la operación. Inténtalo de nuevo.";

    try {
      const detail = (await response.json()).detail;

      if (detail?.message) {
        message = detail.message;
      } else if (detail?.reason === "not_authenticated") {
        message = "Tu sesión terminó. Inicia sesión de nuevo.";
      } else if (detail?.reason === "accounts_unavailable") {
        message =
          "Las cuentas no están disponibles en este momento. La búsqueda sigue funcionando.";
      }
    } catch {
      // Respuesta sin cuerpo JSON: se deja el mensaje general.
    }

    throw new Error(message);
  }

  return response.json();
}

export const fastApiAccountRepository = defineAccountPort({
  current() {
    return call("/auth/me");
  },

  /** Dirección a la que se navega para iniciar sesión con Google. */
  loginUrl() {
    return `${API_URL}/auth/google/login`;
  },

  logout() {
    return call("/auth/logout", { method: "POST" });
  },

  deleteAccount() {
    return call("/auth/me", { method: "DELETE" });
  },

  listDevices() {
    return call("/devices");
  },

  addDevice(device) {
    return call("/devices", { method: "POST", body: device });
  },

  removeDevice(deviceId) {
    return call(`/devices/${encodeURIComponent(deviceId)}`, {
      method: "DELETE",
    });
  },

  listFavorites() {
    return call("/favorites");
  },

  saveFavorite(gameId, favorite) {
    return call(`/favorites/${encodeURIComponent(gameId)}`, {
      method: "PUT",
      body: favorite,
    });
  },

  removeFavorite(gameId) {
    return call(`/favorites/${encodeURIComponent(gameId)}`, {
      method: "DELETE",
    });
  },

  setFavoriteTarget(gameId, targetPrice) {
    return call(`/favorites/${encodeURIComponent(gameId)}/target`, {
      method: "PUT",
      body: { target_price: targetPrice },
    });
  },

  favoriteAlerts() {
    return call("/favorites/alerts");
  },
});
