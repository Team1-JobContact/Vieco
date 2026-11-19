"""Connection options shared by the API, Alembic and snapshot import."""
import ssl
from pathlib import Path

from sqlalchemy.engine import make_url

from src.config.settings import SERVER_DIR


def connection_args(settings) -> dict:
    if make_url(settings.DATABASE_URL).drivername != "mysql+pymysql":
        return {}
    args = {"charset": "utf8mb4", "connect_timeout": 10, "read_timeout": 30, "write_timeout": 30}
    if settings.DATABASE_SSL:
        ca = Path(settings.DATABASE_SSL_CA).expanduser() if settings.DATABASE_SSL_CA else None
        if ca is not None and not ca.is_absolute():
            ca = SERVER_DIR / ca
        # Verify both the certificate chain and hostname; never downgrade TLS.
        args["ssl"] = ssl.create_default_context(cafile=str(ca) if ca else None)
    return args
