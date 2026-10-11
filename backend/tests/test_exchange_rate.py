import httpx

from app.infrastructure.external.exchange import open_exchange_rate_provider
from app.infrastructure.external.exchange.open_exchange_rate_provider import (
    OpenExchangeRateProvider,
)


class _MockResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_exchange_rate_is_fetched_once_and_cached(monkeypatch):
    calls = []

    def mock_get(url, timeout=None):
        calls.append(url)
        return _MockResponse({"rates": {"COP": 4000}})

    monkeypatch.setattr(open_exchange_rate_provider.httpx, "get", mock_get)

    provider = OpenExchangeRateProvider()

    assert provider.usd_to_cop() == 4000.0
    assert provider.usd_to_cop() == 4000.0
    assert len(calls) == 1


def test_exchange_rate_uses_configured_fallback_when_source_fails(monkeypatch):
    def failing_get(*args, **kwargs):
        raise httpx.ConnectError("Tasa de cambio no disponible")

    monkeypatch.setattr(open_exchange_rate_provider.httpx, "get", failing_get)
    monkeypatch.setenv("USD_TO_COP_RATE", "3900")

    assert OpenExchangeRateProvider().usd_to_cop() == 3900.0


def test_exchange_rate_ignores_malformed_response(monkeypatch):
    def mock_get(url, timeout=None):
        return _MockResponse({"result": "error"})

    monkeypatch.setattr(open_exchange_rate_provider.httpx, "get", mock_get)
    monkeypatch.delenv("USD_TO_COP_RATE", raising=False)

    assert OpenExchangeRateProvider().usd_to_cop() == 3250.0
