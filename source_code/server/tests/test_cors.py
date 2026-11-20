import pytest
from pydantic import ValidationError

from src.config.settings import Settings, settings


def test_deployed_frontend_origin_is_normalized_and_restricts_cors():
    config = Settings(_env_file=None, FRONTEND_URL="https://frontend.example.com/")
    assert config.FRONTEND_URL == "https://frontend.example.com"
    assert config.cors_origins == ["https://frontend.example.com"]


@pytest.mark.parametrize("url", ["*", "ftp://frontend.example.com", "https://frontend.example.com/pages/index.html"])
def test_frontend_url_requires_http_origin(url):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, FRONTEND_URL=url)


def test_local_frontend_supports_both_loopback_names():
    config = Settings(_env_file=None, FRONTEND_URL="http://127.0.0.1:5500/")
    assert set(config.cors_origins) == {"http://localhost:5500", "http://127.0.0.1:5500"}


def test_frontend_can_preflight_authenticated_json_requests(client):
    origin = settings.FRONTEND_URL
    response = client.options("/api/v1/auth/login", headers={
        "Origin": origin,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization,content-type",
    })
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert "POST" in response.headers["access-control-allow-methods"]
    assert client.get("/api/v1/health", headers={"Origin": origin}).headers["access-control-allow-origin"] == origin


def test_unconfigured_origin_is_not_allowed(client):
    origin = "https://untrusted.example.com"
    response = client.options("/api/v1/auth/login", headers={
        "Origin": origin,
        "Access-Control-Request-Method": "POST",
    })
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
    assert "access-control-allow-origin" not in client.get("/api/v1/health", headers={"Origin": origin}).headers
