import os
import ssl
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.import_shared_data import preflight, require_empty
from src.config.connection import connection_args
from src.config.settings import settings


def test_cloud_tls_requires_verified_certificate_and_hostname():
    args = connection_args(SimpleNamespace(
        DATABASE_URL="mysql+pymysql://user@cloud.example/db", DATABASE_SSL=True, DATABASE_SSL_CA=""
    ))
    assert args["ssl"].verify_mode == ssl.CERT_REQUIRED
    assert args["ssl"].check_hostname is True


def test_cors_only_allows_configured_frontend(client):
    headers = {"Origin": "https://unrelated.example", "Access-Control-Request-Method": "POST",
               "Access-Control-Request-Headers": "Authorization,Content-Type"}
    denied = client.options("/api/v1/auth/login", headers=headers)
    assert denied.status_code == 400
    assert "access-control-allow-origin" not in denied.headers
    allowed = client.options("/api/v1/auth/login", headers={**headers, "Origin": settings.FRONTEND_URL})
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == settings.FRONTEND_URL


@pytest.mark.parametrize("overrides,message", [
    ({"DEBUG": "true"}, "DEBUG=false"),
    ({"SECRET_KEY": "secret_key_default"}, "private SECRET_KEY"),
    ({"DATABASE_URL": "mysql+pymysql://user@db.aivencloud.com/defaultdb", "DATABASE_SSL": "false"}, "DATABASE_SSL=true"),
])
def test_shared_start_rejects_invalid_deployment_configuration(tmp_path, overrides, message):
    env = dict(os.environ, VIECO_ENV_FILE=str(tmp_path / "absent.env"), DEBUG="false",
               SECRET_KEY="x" * 48, DATABASE_URL="sqlite://")
    env.update(overrides)
    result = subprocess.run([sys.executable, "run_shared.py"], cwd=Path(__file__).resolve().parents[1],
                            env=env, capture_output=True, text=True, timeout=10)
    assert result.returncode != 0
    assert message in result.stderr


def test_missing_ca_fails_before_any_database_connection(tmp_path):
    with pytest.raises(FileNotFoundError):
        connection_args(SimpleNamespace(
            DATABASE_URL="mysql+pymysql://user@cloud.example/db", DATABASE_SSL=True,
            DATABASE_SSL_CA=str(tmp_path / "missing.pem")
        ))


def test_import_refuses_existing_database():
    class Cursor:
        def execute(self, sql):
            assert sql == "SHOW TABLES"  # No write query is allowed before refusal.

        def fetchall(self):
            return [("users",)]

    with pytest.raises(RuntimeError, match="already has tables"):
        require_empty(Cursor())


def test_snapshot_refuses_conflicting_upload_without_overwriting(tmp_path):
    snapshot = tmp_path / "snapshot"
    source = snapshot / "uploads" / "cvs"
    source.mkdir(parents=True)
    (snapshot / "vieco_data.sql").write_text("CREATE TABLE `alembic_version` (version_num varchar(32));")
    (source / "cv.pdf").write_bytes(b"new")
    existing = tmp_path / "uploads" / "cvs"
    existing.mkdir(parents=True)
    (existing / "cv.pdf").write_bytes(b"keep")
    with pytest.raises(RuntimeError, match="no file overwritten"):
        preflight(snapshot, existing.parent)
    assert (existing / "cv.pdf").read_bytes() == b"keep"


def test_snapshot_cannot_switch_target_database(tmp_path):
    (tmp_path / "vieco_data.sql").write_text("USE another_database;\nCREATE TABLE `alembic_version` (id int);")
    with pytest.raises(RuntimeError, match="must not select"):
        preflight(tmp_path, tmp_path / "target")


def test_shared_website_api_readiness_and_private_files(tmp_path):
    code = '''
from fastapi.testclient import TestClient
import src.app as module
with TestClient(module.app) as client:
    assert client.get('/').status_code == 200
    assert client.get('/pages/login.html').status_code == 200
    assert client.get('/src/services/auth-api.js').status_code == 200
    assert client.get('/api/v1/health').status_code == 200
    assert client.get('/api/v1/ready').json() == {'status': 'ready'}
    assert client.get('/uploads/cvs/secret.pdf').status_code == 404
    assert client.get('/.env.shared').status_code == 404
    assert client.get('/package.json').status_code == 404
    assert client.get('/tests/core-ui.test.cjs').status_code == 404
    assert client.get('/web.stdout.log').status_code == 404
    assert client.get('/src/../package.json').status_code == 404
    assert client.get('/api/v1/candidates/me/cvs/1/download').status_code in (401, 403)
    def unavailable():
        raise RuntimeError('private-connection-details')
    module.engine.connect = unavailable
    response = client.get('/api/v1/ready')
    assert response.status_code == 503
    assert response.json() == {'status': 'unavailable'}
'''
    env = dict(os.environ, SERVE_FRONTEND="true", DATABASE_URL="sqlite://", DATABASE_SSL="false",
               UPLOAD_DIR=str(tmp_path / "uploads"), DEBUG="false")
    result = subprocess.run([sys.executable, "-c", code], cwd=Path(__file__).resolve().parents[1],
                            env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
