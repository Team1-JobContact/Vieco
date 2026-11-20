from datetime import timedelta, timezone

from sqlalchemy import MetaData, create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from src.config.settings import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_recycle=3600,
    echo=settings.DEBUG
)

# CURRENT_TIMESTAMP follows the MySQL session clock, while business timestamps
# are generated in UTC by Python. Read the server offset to label defaults.
SERVER_TIMEZONE = timezone.utc
if engine.dialect.name == "mysql":
    @event.listens_for(engine, "connect")
    def read_server_timezone(connection, _):
        global SERVER_TIMEZONE
        with connection.cursor() as cursor:
            cursor.execute("SELECT TIMESTAMPDIFF(SECOND, UTC_TIMESTAMP(), NOW())")
            SERVER_TIMEZONE = timezone(timedelta(seconds=cursor.fetchone()[0]))

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Quy ước đặt tên ràng buộc/chỉ mục cố định để Alembic sinh/so sánh ổn định
# (MySQL giới hạn tên tối đa 64 ký tự).
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

Base = declarative_base(metadata=MetaData(naming_convention=NAMING_CONVENTION))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
