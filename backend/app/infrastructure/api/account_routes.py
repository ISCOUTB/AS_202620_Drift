"""
Rutas de sesión, de dispositivos (ADR-0017), de favoritos (ADR-0020) y de
sus alertas de precio (ADR-0021).

La sesión viaja en una cookie que el código de la página no puede leer
(`HttpOnly`) y que el navegador no envía en peticiones iniciadas por otros
sitios (`SameSite=Lax`). Además, toda petición que cambia datos debe venir
de un origen permitido.
"""

import hmac
import logging
from dataclasses import asdict, dataclass
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field, StrictInt

from app.application.usecases.favorite_alerts import CheckFavoriteAlerts
from app.application.usecases.accounts import (
    DeviceNotFound,
    Devices,
    FavoriteNotFound,
    Favorites,
    Sessions,
)
from app.domain.model.account import (
    Device,
    Favorite,
    InvalidDevice,
    InvalidFavorite,
    User,
)
from app.domain.ports.identity_provider import (
    IdentityProviderUnavailable,
    IdentityRejected,
)
from app.infrastructure.observability import log_event

logger = logging.getLogger("drift")

SESSION_COOKIE = "drift_session"
STATE_COOKIE = "drift_login_state"
NONCE_COOKIE = "drift_login_nonce"

LOGIN_ATTEMPT_SECONDS = 600
SESSION_SECONDS = 30 * 24 * 60 * 60


@dataclass(frozen=True)
class AccountSettings:
    frontend_url: str
    allowed_origins: List[str]
    # Solo por HTTPS; en el equipo de quien desarrolla (http) se desactiva.
    secure_cookies: bool


class PcSpecsRequest(BaseModel):
    ram_gb: StrictInt
    gpu_score: StrictInt
    gpu_name: Optional[str] = Field(default=None, max_length=120)
    cpu_name: Optional[str] = Field(default=None, max_length=120)
    cpu_score: Optional[StrictInt] = None
    storage_gb: Optional[StrictInt] = None


class DeviceRequest(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    kind: Literal["pc", "playstation", "xbox"]
    specs: Optional[PcSpecsRequest] = None


class FavoriteRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    image: Optional[str] = Field(default=None, max_length=500)
    # Mejor precio que la persona tenía en pantalla al guardar, y su tienda.
    price: Optional[float] = Field(default=None, ge=0, le=1_000_000_000)
    store: Optional[str] = Field(default=None, min_length=1, max_length=60)


class FavoriteTargetRequest(BaseModel):
    # `null` quita el precio objetivo.
    target_price: Optional[float] = Field(default=None, gt=0, le=1_000_000_000)


def _favorite_json(favorite: Favorite) -> dict:
    return {
        "game_id": favorite.game_id,
        "name": favorite.name,
        "image": favorite.image,
        "price": favorite.price,
        "store": favorite.store,
        "saved_at": favorite.saved_at.isoformat() if favorite.saved_at else None,
        "target_price": favorite.target_price,
    }


def _alerts_json(answer) -> dict:
    return {
        "checked_at": answer.checked_at.isoformat(),
        "alerts": answer.alerts,
        "items": [
            {
                "game_id": status.favorite.game_id,
                "current": (
                    {"store": status.current.store, "price": status.current.price}
                    if status.current
                    else None
                ),
                "alert": (
                    {
                        "reason": status.alert.reason,
                        "saved_difference": status.alert.saved_difference,
                    }
                    if status.alert
                    else None
                ),
            }
            for status in answer.statuses
        ],
    }


def _user_json(user: User) -> dict:
    # El identificador interno y el de Google no salen del servidor.
    return {"name": user.name, "email": user.email, "picture": user.picture}


def _device_json(device: Device) -> dict:
    return {
        "id": device.id,
        "name": device.name,
        "kind": device.kind,
        "specs": asdict(device.specs) if device.specs else None,
    }


# Errores del dominio que la API traduce: (tipo, estado HTTP, motivo, con mensaje).
INVALID_DEVICE = (InvalidDevice, 422, "invalid_device", True)
DEVICE_NOT_FOUND = (DeviceNotFound, 404, "device_not_found", False)
INVALID_FAVORITE = (InvalidFavorite, 422, "invalid_favorite", True)
FAVORITE_NOT_FOUND = (FavoriteNotFound, 404, "favorite_not_found", False)

GAME_ID_PATTERN = r"^[A-Za-z0-9_-]{1,80}$"

_DESCRIPTIONS = {
    401: "No hay sesión.",
    403: "La petición no viene de un origen permitido.",
    404: "El inicio de sesión no está configurado o el elemento no existe.",
    422: "Datos inválidos.",
    503: "El almacén de cuentas no respondió.",
}


def _responses(*codes: int) -> dict:
    return {code: {"description": _DESCRIPTIONS[code]} for code in codes}


def _game_id_path():
    return Path(..., pattern=GAME_ID_PATTERN)


class _AccountApi:
    """
    Lo que hacen las rutas de cuentas. `build_account_router` solo las
    registra: aquí viven las comprobaciones y la traducción de errores.
    """

    def __init__(
        self,
        sessions: Optional[Sessions],
        devices: Optional[Devices],
        settings: AccountSettings,
        favorites: Optional[Favorites],
        favorite_alerts: Optional[CheckFavoriteAlerts],
    ):
        self.sessions = sessions
        self.devices = devices
        self.settings = settings
        self.favorites = favorites
        self.favorite_alerts = favorite_alerts
        self.login_available = sessions is not None and devices is not None

    # --- Errores -----------------------------------------------------------------

    @staticmethod
    def unavailable(error: Exception) -> HTTPException:
        # Solo el tipo: el mensaje podría traer datos de conexión.
        log_event(logger, "accounts_unavailable", error=type(error).__name__)

        return HTTPException(
            status_code=503,
            detail={"reason": "accounts_unavailable"},
        )

    def run(self, action, *known):
        """Ejecuta `action`; un error conocido es su respuesta, otro es un 503."""

        try:
            return action()
        except Exception as error:  # noqa: BLE001  cualquier fallo del almacén
            for kind, status, reason, with_message in known:
                if isinstance(error, kind):
                    detail = {"reason": reason}

                    if with_message:
                        detail["message"] = str(error)

                    raise HTTPException(status_code=status, detail=detail) from error

            raise self.unavailable(error) from error

    # --- Dependencias ----------------------------------------------------------

    def require_login_available(self) -> None:
        if not self.login_available:
            raise HTTPException(
                status_code=404,
                detail={"reason": "login_not_configured"},
            )

    def require_favorites(self) -> None:
        if self.favorites is None:
            raise HTTPException(
                status_code=404,
                detail={"reason": "login_not_configured"},
            )

    def require_alerts(self) -> None:
        if self.favorite_alerts is None:
            raise HTTPException(
                status_code=404,
                detail={"reason": "login_not_configured"},
            )

    def find_user(self, request: Request) -> Optional[User]:
        if not self.login_available:
            return None

        return self.run(
            lambda: self.sessions.current_user(request.cookies.get(SESSION_COOKIE))
        )

    def require_user(self, request: Request) -> User:
        self.require_login_available()
        user = self.find_user(request)

        if user is None:
            raise HTTPException(
                status_code=401,
                detail={"reason": "not_authenticated"},
            )

        return user

    def require_trusted_origin(self, request: Request) -> None:
        """Una petición que cambia datos debe venir de la página de DRIFT."""

        if request.headers.get("origin") not in self.settings.allowed_origins:
            raise HTTPException(
                status_code=403,
                detail={"reason": "untrusted_origin"},
            )

    # --- Cookies -----------------------------------------------------------------

    def set_cookie(self, response, name: str, value: str, max_age: int) -> None:
        response.set_cookie(
            name,
            value,
            max_age=max_age,
            httponly=True,
            secure=self.settings.secure_cookies,
            samesite="lax",
            path="/",
        )

    def clear_cookie(self, response, name: str) -> None:
        response.delete_cookie(
            name,
            httponly=True,
            secure=self.settings.secure_cookies,
            samesite="lax",
            path="/",
        )

    def back_to_frontend(self, result: str) -> RedirectResponse:
        frontend_url = self.settings.frontend_url
        separator = "&" if "?" in frontend_url else "?"
        response = RedirectResponse(
            f"{frontend_url}{separator}login={result}",
            status_code=303,
        )
        self.clear_cookie(response, STATE_COOKIE)
        self.clear_cookie(response, NONCE_COOKIE)

        return response

    # --- Sesión --------------------------------------------------------------------

    def me(self, request: Request) -> dict:
        user = self.find_user(request)

        return {
            "login_available": self.login_available,
            "authenticated": user is not None,
            "user": _user_json(user) if user else None,
        }

    def begin_login(self) -> RedirectResponse:
        attempt = self.sessions.begin()
        response = RedirectResponse(attempt["url"], status_code=303)

        self.set_cookie(response, STATE_COOKIE, attempt["state"], LOGIN_ATTEMPT_SECONDS)
        self.set_cookie(response, NONCE_COOKIE, attempt["nonce"], LOGIN_ATTEMPT_SECONDS)

        return response

    def complete_login(
        self,
        request: Request,
        code: Optional[str],
        state: Optional[str],
    ) -> RedirectResponse:
        expected_state = request.cookies.get(STATE_COOKIE)
        nonce = request.cookies.get(NONCE_COOKIE)

        # Sin el `state` que este navegador recibió al empezar, el inicio de
        # sesión no lo pidió esta persona.
        if not (code and state and expected_state and nonce) or not hmac.compare_digest(
            state.encode(), expected_state.encode()
        ):
            log_event(logger, "login_rejected", reason="state_mismatch")
            return self.back_to_frontend("error")

        try:
            session = self.sessions.complete(code, nonce)
        except IdentityRejected as error:
            log_event(logger, "login_rejected", reason=str(error))
            return self.back_to_frontend("error")
        except IdentityProviderUnavailable:
            log_event(logger, "login_rejected", reason="provider_unavailable")
            return self.back_to_frontend("unavailable")
        except Exception as error:  # noqa: BLE001  fallo del almacén de cuentas
            log_event(logger, "accounts_unavailable", error=type(error).__name__)
            return self.back_to_frontend("unavailable")

        log_event(logger, "login_completed")

        response = self.back_to_frontend("ok")
        self.set_cookie(response, SESSION_COOKIE, session["token"], SESSION_SECONDS)

        return response

    def logout(self, request: Request) -> JSONResponse:
        if self.login_available:
            self.run(lambda: self.sessions.end(request.cookies.get(SESSION_COOKIE)))

        response = JSONResponse({"authenticated": False})
        self.clear_cookie(response, SESSION_COOKIE)

        return response

    def delete_account(self, user: User) -> JSONResponse:
        self.run(lambda: self.sessions.delete_account(user))
        log_event(logger, "account_deleted")

        response = JSONResponse({"deleted": True})
        self.clear_cookie(response, SESSION_COOKIE)

        return response

    # --- Dispositivos ----------------------------------------------------------

    def list_devices(self, user: User) -> list:
        return self.run(
            lambda: [_device_json(device) for device in self.devices.list(user)]
        )

    def save_device(self, action) -> dict:
        return _device_json(self.run(action, INVALID_DEVICE, DEVICE_NOT_FOUND))

    def delete_device(self, user: User, device_id: str) -> dict:
        self.run(lambda: self.devices.remove(user, device_id), DEVICE_NOT_FOUND)

        return {"deleted": True}

    # --- Favoritos y alertas -----------------------------------------------------

    def check_alerts(self, user: User) -> dict:
        return self.run(lambda: _alerts_json(self.favorite_alerts.execute(user)))

    def set_target(self, user: User, game_id: str, target_price) -> dict:
        return _favorite_json(
            self.run(
                lambda: self.favorites.set_target(user, game_id, target_price),
                FAVORITE_NOT_FOUND,
                INVALID_FAVORITE,
            )
        )

    def list_favorites(self, user: User) -> list:
        return self.run(
            lambda: [_favorite_json(item) for item in self.favorites.list(user)]
        )

    def save_favorite(self, user: User, game_id: str, body: "FavoriteRequest") -> dict:
        return _favorite_json(
            self.run(
                lambda: self.favorites.save(
                    user,
                    game_id,
                    body.name,
                    body.image,
                    body.price,
                    body.store,
                ),
                INVALID_FAVORITE,
            )
        )

    def delete_favorite(self, user: User, game_id: str) -> dict:
        self.run(lambda: self.favorites.remove(user, game_id), FAVORITE_NOT_FOUND)

        return {"deleted": True}


def _specs(body: DeviceRequest):
    return body.specs.model_dump() if body.specs else None


def build_account_router(
    sessions: Optional[Sessions],
    devices: Optional[Devices],
    settings: AccountSettings,
    favorites: Optional[Favorites] = None,
    favorite_alerts: Optional[CheckFavoriteAlerts] = None,
) -> APIRouter:
    """`sessions` y `devices` son `None` si el inicio de sesión no está configurado.

    Solo registra las rutas: cada una delega en `_AccountApi`.
    """

    api = _AccountApi(sessions, devices, settings, favorites, favorite_alerts)
    router = APIRouter()

    login = [Depends(api.require_login_available)]
    trusted = [Depends(api.require_trusted_origin)]
    with_favorites = [Depends(api.require_favorites), Depends(api.require_trusted_origin)]

    @router.get("/auth/me", responses=_responses(503))
    def me(request: Request):
        return api.me(request)

    @router.get("/auth/google/login", dependencies=login, responses=_responses(404))
    def google_login():
        return api.begin_login()

    @router.get("/auth/google/callback", dependencies=login, responses=_responses(404))
    def google_callback(
        request: Request,
        code: Optional[str] = None,
        state: Optional[str] = None,
    ):
        return api.complete_login(request, code, state)

    @router.post("/auth/logout", dependencies=trusted, responses=_responses(403, 503))
    def logout(request: Request):
        return api.logout(request)

    @router.delete(
        "/auth/me",
        dependencies=trusted,
        responses=_responses(401, 403, 404, 503),
    )
    def delete_account(user: User = Depends(api.require_user)):
        return api.delete_account(user)

    @router.get("/devices", responses=_responses(401, 404, 503))
    def list_devices(user: User = Depends(api.require_user)):
        return api.list_devices(user)

    @router.post(
        "/devices",
        status_code=201,
        dependencies=trusted,
        responses=_responses(401, 403, 404, 422, 503),
    )
    def add_device(body: DeviceRequest, user: User = Depends(api.require_user)):
        return api.save_device(
            lambda: devices.add(user, body.name, body.kind, _specs(body))
        )

    @router.put(
        "/devices/{device_id}",
        dependencies=trusted,
        responses=_responses(401, 403, 404, 422, 503),
    )
    def update_device(
        device_id: str,
        body: DeviceRequest,
        user: User = Depends(api.require_user),
    ):
        return api.save_device(
            lambda: devices.update(user, device_id, body.name, body.kind, _specs(body))
        )

    @router.delete(
        "/devices/{device_id}",
        dependencies=trusted,
        responses=_responses(401, 403, 404, 503),
    )
    def delete_device(device_id: str, user: User = Depends(api.require_user)):
        return api.delete_device(user, device_id)

    # Va antes de /favorites/{game_id} para que «alerts» no se lea como un juego.
    @router.get(
        "/favorites/alerts",
        dependencies=[Depends(api.require_alerts)],
        responses=_responses(401, 404, 503),
    )
    def check_alerts(user: User = Depends(api.require_user)):
        return api.check_alerts(user)

    # «alerts» es una dirección reservada, no un juego: sin esto, `PUT` y
    # `DELETE` caerían en /favorites/{game_id} y guardarían un favorito
    # llamado «alerts».
    @router.api_route(
        "/favorites/alerts",
        methods=["PUT", "DELETE", "POST", "PATCH", "OPTIONS"],
        include_in_schema=False,
    )
    def alerts_method_not_allowed():
        return JSONResponse(
            {"detail": "Method Not Allowed"},
            status_code=405,
            headers={"Allow": "GET"},
        )

    @router.put(
        "/favorites/{game_id}/target",
        dependencies=with_favorites,
        responses=_responses(401, 403, 404, 422, 503),
    )
    def set_favorite_target(
        body: FavoriteTargetRequest,
        game_id: str = _game_id_path(),
        user: User = Depends(api.require_user),
    ):
        return api.set_target(user, game_id, body.target_price)

    @router.get(
        "/favorites",
        dependencies=[Depends(api.require_favorites)],
        responses=_responses(401, 404, 503),
    )
    def list_favorites(user: User = Depends(api.require_user)):
        return api.list_favorites(user)

    @router.put(
        "/favorites/{game_id}",
        dependencies=with_favorites,
        responses=_responses(401, 403, 404, 422, 503),
    )
    def save_favorite(
        body: FavoriteRequest,
        game_id: str = _game_id_path(),
        user: User = Depends(api.require_user),
    ):
        return api.save_favorite(user, game_id, body)

    @router.delete(
        "/favorites/{game_id}",
        dependencies=with_favorites,
        responses=_responses(401, 403, 404, 422, 503),
    )
    def delete_favorite(
        game_id: str = _game_id_path(),
        user: User = Depends(api.require_user),
    ):
        return api.delete_favorite(user, game_id)

    return router
