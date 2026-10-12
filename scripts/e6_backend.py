"""Inicia el backend de DRIFT apuntando al upstream simulado del experimento E6.

No modifica el código medido: antes de importar la aplicación redirige las
llamadas `httpx.get` de los adaptadores hacia `scripts/stub_upstream.py`. Así
la misma envoltura sirve para la versión anterior y la posterior al cambio.

Uso:
    python scripts/e6_backend.py <carpeta backend> [puerto]
"""

import json
import os
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request

import httpx
import uvicorn

STUB_URL = os.getenv("E6_STUB_URL", "http://127.0.0.1:9100")

UPSTREAMS = {
    "https://store.steampowered.com": f"{STUB_URL}/steam",
    "https://www.cheapshark.com": f"{STUB_URL}/cheapshark",
    "https://store.playstation.com": f"{STUB_URL}/playstation",
    "https://open.er-api.com": f"{STUB_URL}/exchange",
}

# Transporte del experimento. `httpx.get` crea un cliente (y su contexto TLS)
# en cada llamada; en el equipo de medicion eso cuesta ~0,5 s de CPU por
# llamada y taparia el efecto que se quiere medir. Aqui cada llamada usa una
# conexion HTTP simple de la biblioteca estandar. Se aplica igual a la version
# anterior y a la posterior.
class _StubResponse:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return json.loads(self._body)


def _stubbed_get(url, params=None, headers=None, timeout=5.0, **kwargs):
    for real_prefix, stub_prefix in UPSTREAMS.items():
        if url.startswith(real_prefix):
            target = stub_prefix + url[len(real_prefix):]

            if params:
                target += "?" + urllib.parse.urlencode(params)

            request = urllib.request.Request(target, headers=headers or {})

            try:
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    return _StubResponse(response.status, response.read())
            except urllib.error.HTTPError as error:
                return _StubResponse(error.code, error.read())
            except (TimeoutError, socket.timeout) as error:
                raise httpx.ReadTimeout(str(error)) from error
            except OSError as error:
                if isinstance(getattr(error, "reason", None), (TimeoutError, socket.timeout)):
                    raise httpx.ReadTimeout(str(error)) from error

                raise httpx.ConnectError(str(error)) from error

    # El experimento no debe tocar ningún servicio real.
    raise RuntimeError(f"URL sin upstream simulado: {url}")


def main():
    backend_dir = os.path.abspath(sys.argv[1])
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8100

    httpx.get = _stubbed_get

    os.chdir(backend_dir)
    sys.path.insert(0, backend_dir)

    # Un worker, como declara el escenario E6.
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=port,
        workers=1,
        log_level="warning",
    )


if __name__ == "__main__":
    main()
