import time
from threading import Event, Lock
from typing import Any, Callable, Hashable


class _Flight:
    """Carga en curso de una clave; quienes llegan después esperan su resultado."""

    def __init__(self):
        self.done = Event()
        self.value = None
        self.error = None


class SingleFlightCache:
    """
    Caché con vencimiento y una sola carga en vuelo por clave.

    El lock protege solo los diccionarios, nunca la llamada externa: dos
    búsquedas distintas no se esperan entre sí, y dos búsquedas iguales
    comparten una única consulta a la fuente.
    """

    def __init__(self, ttl_seconds: float):
        self._ttl_seconds = ttl_seconds
        self._entries = {}
        self._flights = {}
        self._lock = Lock()

    def get_or_load(self, key: Hashable, loader: Callable[[], Any]) -> Any:
        with self._lock:
            entry = self._entries.get(key)

            if entry and time.monotonic() - entry[0] < self._ttl_seconds:
                return entry[1]

            flight = self._flights.get(key)
            is_owner = flight is None

            if is_owner:
                flight = _Flight()
                self._flights[key] = flight

        if not is_owner:
            flight.done.wait()

            if flight.error is not None:
                raise flight.error

            return flight.value

        try:
            value = loader()
        except BaseException as error:
            # Los errores no se guardan: la siguiente búsqueda reintenta.
            flight.error = error
            raise
        else:
            flight.value = value

            with self._lock:
                self._discard_expired()
                self._entries[key] = (time.monotonic(), value)

            return value
        finally:
            with self._lock:
                self._flights.pop(key, None)

            flight.done.set()

    def _discard_expired(self) -> None:
        now = time.monotonic()

        for key in [
            key
            for key, (created_at, _) in self._entries.items()
            if now - created_at >= self._ttl_seconds
        ]:
            del self._entries[key]
