"""Serve the website and API from one host, sharing the backend uploads directory."""
import os
from pathlib import Path

import uvicorn

if __name__ == "__main__":
    os.chdir(Path(__file__).resolve().parent)
    os.environ.setdefault("VIECO_ENV_FILE", ".env.shared")
    os.environ["SERVE_FRONTEND"] = "true"
    from src.config.settings import Settings, settings
    from sqlalchemy.engine import make_url

    if settings.DEBUG:
        raise SystemExit("Shared server requires DEBUG=false.")
    if len(settings.SECRET_KEY) < 32 or settings.SECRET_KEY in ("secret_key_default", "replace-with-a-long-random-secret"):
        raise SystemExit("Set a private SECRET_KEY of at least 32 characters in the shared environment.")
    if settings.DATABASE_URL == Settings.model_fields["DATABASE_URL"].default:
        raise SystemExit("Set DATABASE_URL explicitly in the shared environment.")
    host = make_url(settings.DATABASE_URL).host or ""
    if host.endswith(".aivencloud.com") and not settings.DATABASE_SSL:
        raise SystemExit("Aiven requires DATABASE_SSL=true and its CA certificate.")
    uvicorn.run("src.app:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
