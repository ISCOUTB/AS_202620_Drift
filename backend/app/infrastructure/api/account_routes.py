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


def build_account_router(
    sessions: Optional[Sessions],
    devices: Optional[Devices],
    settings: AccountSettings,
    favorites: Optional[Favorites] = None,
    favorite_alerts: Optional[CheckFavoriteAlerts] = None,
) -> APIRouter:
    """`sessions` y `devices` son `None` si el inicio de sesión no está configurado."""

    router = APIRouter()
    login_available = sessions is not None and devices is not None

    def unavailable(error: Exception) -> HTTPException:
        # Solo el tipo: el mensaje podría traer datos de conexión.
        log_event(logger, "accounts_unavailable", error=type(error).__name__)

        return HTTPException(
            status_code=503,
            detail={"reason": "accounts_unavailable"},
        )

    def require_login_available() -> None:
        if not login_available:
            raise HTTPException(
                status_code=404,
                detail={"reason": "login_not_configured"},
            )

    def find_user(request: Request) -> Optional[User]:
        if not login_available:
            return None

        try:
            return sessions.current_user(request.cookies.get(SESSION_COOKIE))
        except Exception as error:  # noqa: BLE001  cualquier fallo del almacén
            raise unavailable(error) from error

    def require_user(request: Request) -> User:
        require_login_available()
        user = find_user(request)

        if user is None:
            raise HTTPException(
                status_code=401,
                detail={"reason": "not_authenticated"},
            )

        return user

    def require_trusted_origin(request: Request) -> None:
        """Una petición que cambia datos debe venir de la página de DRIFT."""

        if request.headers.get("origin") not in settings.allowed_origins:
            raise HTTPException(
                status_code=403,
                detail={"reason": "untrusted_origin"},
            )

    def set_cookie(response, name: str, value: str, max_age: int) -> None:
        response.set_cookie(
            name,
            value,
            max_age=max_age,
            httponly=True,
            secure=settings.secure_cookies,
            samesite="lax",
            path="/",
        )

    def clear_cookie(response, name: str) -> None:
        response.delete_cookie(
            name,
            httponly=True,
            secure=settings.secure_cookies,
            samesite="lax",
            path="/",
        )

    def back_to_frontend(result: str) -> RedirectResponse:
        separator = "&" if "?" in settings.frontend_url else "?"
        response = RedirectResponse(
            f"{settings.frontend_url}{separator}login={result}",
            status_code=303,
        )
        clear_cookie(response, STATE_COOKIE)
        clear_cookie(response, NONCE_COOKIE)

        return response

    @router.get("/auth/me")
    def me(request: Request):
        user = find_user(request)

        return {
            "login_available": login_available,
            "authenticated": user is not None,
            "user": _user_json(user) if user else None,
        }

    @router.get("/auth/google/login", dependencies=[Depends(require_login_available)])
    def google_login():
        attempt = sessions.begin()
        response = RedirectResponse(attempt["url"], status_code=303)

        set_cookie(response, STATE_COOKIE, attempt["state"], LOGIN_ATTEMPT_SECONDS)
        set_cookie(response, NONCE_COOKIE, attempt["nonce"], LOGIN_ATTEMPT_SECONDS)

        return response

    @router.get(
        "/auth/google/callback",
        dependencies=[Depends(require_login_available)],
    )
    def google_callback(
        request: Request,
        code: Optional[str] = None,
        state: Optional[str] = None,
    ):
        expected_state = request.cookies.get(STATE_COOKIE)
        nonce = request.cookies.get(NONCE_COOKIE)

        # Sin el `state` que este navegador recibió al empezar, el inicio de
        # sesión no lo pidió esta persona.
        if (
            not code
            or not state
            or not expected_state
            or not nonce
            or not hmac.compare_digest(state.encode(), expected_state.encode())
        ):
            log_event(logger, "login_rejected", reason="state_mismatch")
            return back_to_frontend("error")

        try:
            session = sessions.complete(code, nonce)
        except IdentityRejected as error:
            log_event(logger, "login_rejected", reason=str(error))
            return back_to_frontend("error")
        except IdentityProviderUnavailable:
            log_event(logger, "login_rejected", reason="provider_unavailable")
            return back_to_frontend("unavailable")
        except Exception as error:  # noqa: BLE001  fallo del almacén de cuentas
            log_event(logger, "accounts_unavailable", error=type(error).__name__)
            return back_to_frontend("unavailable")

        log_event(logger, "login_completed")

        response = back_to_frontend("ok")
        set_cookie(response, SESSION_COOKIE, session["token"], SESSION_SECONDS)

        return response

    @router.post("/auth/logout", dependencies=[Depends(require_trusted_origin)])
    def logout(request: Request):
        if login_available:
            try:
                sessions.end(request.cookies.get(SESSION_COOKIE))
            except Exception as error:  # noqa: BLE001
                raise unavailable(error) from error

        response = JSONResponse({"authenticated": False})
        clear_cookie(response, SESSION_COOKIE)

        return response

    @router.delete("/auth/me", dependencies=[Depends(require_trusted_origin)])
    def delete_account(user: User = Depends(require_user)):
        try:
            sessions.delete_account(user)
        except Exception as error:  # noqa: BLE001
            raise unavailable(error) from error

        log_event(logger, "account_deleted")

        response = JSONResponse({"deleted": True})
        clear_cookie(response, SESSION_COOKIE)

        return response

    @router.get("/devices")
    def list_devices(user: User = Depends(require_user)):
        try:
            return [_device_json(device) for device in devices.list(user)]
        except Exception as error:  # noqa: BLE001
            raise unavailable(error) from error

    def save(action):
        try:
            return _device_json(action())
        except InvalidDevice as error:
            raise HTTPException(
                status_code=422,
                detail={"reason": "invalid_device", "message": str(error)},
            ) from error
        except DeviceNotFound as error:
            raise HTTPException(
                status_code=404,
                detail={"reason": "device_not_found"},
            ) from error
        except Exception as error:  # noqa: BLE001
            raise unavailable(error) from error

    @router.post(
        "/devices",
        status_code=201,
        dependencies=[Depends(require_trusted_origin)],
    )
    def add_device(body: DeviceRequest, user: User = Depends(require_user)):
        return save(
            lambda: devices.add(
                user,
                body.name,
                body.kind,
                body.specs.model_dump() if body.specs else None,
            )
        )

    @router.put(
        "/devices/{device_id}",
        dependencies=[Depends(require_trusted_origin)],
    )
    def update_device(
        device_id: str,
        body: DeviceRequest,
        user: User = Depends(require_user),
    ):
        return save(
            lambda: devices.update(
                user,
                device_id,
                body.name,
                body.kind,
                body.specs.model_dump() if body.specs else None,
            )
        )

    @router.delete(
        "/devices/{device_id}",
        dependencies=[Depends(require_trusted_origin)],
    )
    def delete_device(device_id: str, user: User = Depends(require_user)):
        try:
            devices.remove(user, device_id)
        except DeviceNotFound as error:
            raise HTTPException(
                status_code=404,
                detail={"reason": "device_not_found"},
            ) from error
        except Exception as error:  # noqa: BLE001
            raise unavailable(error) from error

        return {"deleted": True}

    def require_favorites() -> None:
        if favorites is None:
            raise HTTPException(
                status_code=404,
                detail={"reason": "login_not_configured"},
            )

    def require_alerts() -> None:
        if favorite_alerts is None:
            raise HTTPException(
                status_code=404,
                detail={"reason": "login_not_configured"},
            )

    # Va antes de /favorites/{game_id} para que «alerts» no se lea como un juego.
    @router.get("/favorites/alerts", dependencies=[Depends(require_alerts)])
    def check_alerts(user: User = Depends(require_user)):
        try:
            return _alerts_json(favorite_alerts.execute(user))
        except Exception as error:  # noqa: BLE001  el almacén de cuentas falló
            raise unavailable(error) from error

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
        dependencies=[Depends(require_favorites), Depends(require_trusted_origin)],
    )
    def set_favorite_target(
        body: FavoriteTargetRequest,
        game_id: str = Path(..., pattern=r"^[A-Za-z0-9_-]{1,80}$"),
        user: User = Depends(require_user),
    ):
        try:
            return _favorite_json(
                favorites.set_target(user, game_id, body.target_price)
            )
        except FavoriteNotFound as error:
            raise HTTPException(
                status_code=404,
                detail={"reason": "favorite_not_found"},
            ) from error
        except InvalidFavorite as error:
            raise HTTPException(
                status_code=422,
                detail={"reason": "invalid_favorite", "message": str(error)},
            ) from error
        except Exception as error:  # noqa: BLE001
            raise unavailable(error) from error

    @router.get("/favorites", dependencies=[Depends(require_favorites)])
    def list_favorites(user: User = Depends(require_user)):
        try:
            return [_favorite_json(item) for item in favorites.list(user)]
        except Exception as error:  # noqa: BLE001
            raise unavailable(error) from error

    @router.put(
        "/favorites/{game_id}",
        dependencies=[Depends(require_favorites), Depends(require_trusted_origin)],
    )
    def save_favorite(
        body: FavoriteRequest,
        game_id: str = Path(..., pattern=r"^[A-Za-z0-9_-]{1,80}$"),
        user: User = Depends(require_user),
    ):
        try:
            return _favorite_json(
                favorites.save(
                    user,
                    game_id,
                    body.name,
                    body.image,
                    body.price,
                    body.store,
                )
            )
        except InvalidFavorite as error:
            raise HTTPException(
                status_code=422,
                detail={"reason": "invalid_favorite", "message": str(error)},
            ) from error
        except Exception as error:  # noqa: BLE001
            raise unavailable(error) from error

    @router.delete(
        "/favorites/{game_id}",
        dependencies=[Depends(require_favorites), Depends(require_trusted_origin)],
    )
    def delete_favorite(
        game_id: str = Path(..., pattern=r"^[A-Za-z0-9_-]{1,80}$"),
        user: User = Depends(require_user),
    ):
        try:
            favorites.remove(user, game_id)
        except FavoriteNotFound as error:
            raise HTTPException(
                status_code=404,
                detail={"reason": "favorite_not_found"},
            ) from error
        except Exception as error:  # noqa: BLE001
            raise unavailable(error) from error

        return {"deleted": True}

    return router
