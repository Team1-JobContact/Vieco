"""Import a trusted mysqldump snapshot into an EMPTY shared database.

Run from server/: python -m scripts.import_shared_data SNAPSHOT_DIRECTORY [--apply]
Without --apply this only validates files and inspects the target database.
"""
import argparse
import re
import shutil
from pathlib import Path

from pymysql.constants import CLIENT
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

from src.config.connection import connection_args
from src.config.settings import SERVER_DIR, Settings


def preflight(snapshot: Path, destination: Path):
    sql = (snapshot / "vieco_data.sql").read_text(encoding="utf-8-sig")
    if re.search(r"^\s*(?:USE\s|(?:CREATE|DROP|ALTER)\s+DATABASE\b)", sql, re.I | re.M):
        raise RuntimeError("Dump must not select, create or drop a database.")
    tables = re.findall(r"^CREATE TABLE `([^`]+)`", sql, re.M)
    if "alembic_version" not in tables:
        raise RuntimeError("Snapshot does not contain the project's migration version.")
    source = snapshot / "uploads"
    if not source.is_dir() or source.is_symlink():
        raise RuntimeError("Snapshot must include an uploads directory.")
    if destination.is_symlink():
        raise RuntimeError("Uploads destination must not be a symlink.")
    files = []
    for item in source.rglob("*"):
        if item.is_symlink():
            raise RuntimeError("Symlinks are not allowed in the snapshot.")
        if not item.is_file():
            continue
        relative = item.relative_to(source)
        if relative.parts[0] not in ("company", "cvs") and relative != Path(".gitkeep"):
            raise RuntimeError("Unexpected file outside company/ and cvs/.")
        target = destination / relative
        if not target.resolve().is_relative_to(destination.resolve()):
            raise RuntimeError("Uploads target escapes its storage directory.")
        if target.exists() and (not target.is_file() or item.read_bytes() != target.read_bytes()):
            raise RuntimeError(f"Existing upload differs; no file overwritten: {relative}")
        files.append((item, target))
    return sql, tables, files


def require_empty(cursor):
    cursor.execute("SHOW TABLES")
    if cursor.fetchall():
        raise RuntimeError("Target database already has tables. Import refused; no existing tables were changed.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--env-file", type=Path, default=SERVER_DIR / ".env.shared")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if not args.env_file.is_file():
        raise RuntimeError("Shared environment file is missing.")
    settings = Settings(_env_file=args.env_file)
    url = make_url(settings.DATABASE_URL)
    if url.drivername != "mysql+pymysql" or not settings.DATABASE_SSL:
        raise RuntimeError("Shared import requires mysql+pymysql and DATABASE_SSL=true.")
    destination = Path(settings.UPLOAD_DIR).expanduser()
    if not destination.is_absolute():
        destination = SERVER_DIR / destination
    sql, tables, files = preflight(args.snapshot.resolve(), destination)
    print(f"Target: {url.host}:{url.port}/{url.database}; tables: {len(tables)}; upload files: {len(files)}")
    options = connection_args(settings)
    options["client_flag"] = CLIENT.MULTI_STATEMENTS
    engine = create_engine(settings.DATABASE_URL, connect_args=options)
    try:
        raw = engine.raw_connection()
        try:
            connection = raw.driver_connection
            with connection.cursor() as cursor:
                cursor.execute("SHOW SESSION STATUS LIKE 'Ssl_cipher'")
                if not cursor.fetchone()[1]:
                    raise RuntimeError("Server did not negotiate TLS; import refused.")
                require_empty(cursor)
                if not args.apply:
                    print("Preflight OK. No data written. Add --apply to import into this empty database.")
                    return
                # Copy only missing files. Never overwrite existing uploads.
                for source, target in files:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if not target.exists():
                        with target.open("xb") as out, source.open("rb") as incoming:
                            shutil.copyfileobj(incoming, out)
                connection.autocommit(True)
                try:
                    cursor.execute(sql)
                    while cursor.nextset():
                        pass
                except Exception as exc:
                    code = exc.args[0] if exc.args and isinstance(exc.args[0], int) else type(exc).__name__
                    raise RuntimeError(f"Import failed ({code}). MySQL DDL can leave a partial import; inspect the target before retrying.") from None
                cursor.execute("SHOW TABLES")
                imported = {row[0] for row in cursor.fetchall()}
                if not set(tables).issubset(imported):
                    raise RuntimeError("Imported schema is incomplete; inspect the target.")
                cursor.execute("SELECT version_num FROM alembic_version")
                print(f"Imported {len(tables)} tables; migration: {cursor.fetchone()[0]}; uploads available: {len(files)}")
        finally:
            raw.close()
    finally:
        engine.dispose()


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError) as exc:
        raise SystemExit(str(exc)) from None
    except Exception as exc:
        # Driver errors can contain SQL/private data; keep those out of logs.
        raise SystemExit(f"Connection/import failed ({type(exc).__name__}). Check CA certificate, credentials and network.") from None
