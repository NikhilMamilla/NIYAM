import httpx
import pytest


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """No test may make a real HTTP request: providers are exercised through httpx.MockTransport only."""
    def refuse(self, request):
        raise RuntimeError(f"tests must not use the network (attempted {request.method} {request.url.host})")
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", refuse)
