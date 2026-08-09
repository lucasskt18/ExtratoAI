from collections.abc import Generator
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(
    settings.resolved_database_url(),
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _alembic_config() -> Config:
    backend_root = Path(__file__).resolve().parent.parent
    cfg = Config(str(backend_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend_root / "alembic"))
    cfg.set_main_option("sqlalchemy.url", settings.resolved_database_url())
    return cfg


def _bootstrap_existing_schema() -> None:
    """Stamp legacy DBs created with metadata.create_all before Alembic."""
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if "alembic_version" in tables or "statements" not in tables:
        return
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS alembic_version ("
                "version_num VARCHAR(32) NOT NULL PRIMARY KEY)"
            )
        )
        conn.execute(text("DELETE FROM alembic_version"))
        conn.execute(
            text("INSERT INTO alembic_version (version_num) VALUES ('0001_initial')")
        )


def run_migrations() -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    _bootstrap_existing_schema()
    command.upgrade(_alembic_config(), "head")


def init_db() -> None:
    from app.db import seed  # noqa: F401
    from app.models import Category, MerchantRule, Statement, Transaction  # noqa: F401

    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.inbox_dir.mkdir(parents=True, exist_ok=True)
    settings.processed_dir.mkdir(parents=True, exist_ok=True)
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    run_migrations()
    with SessionLocal() as db:
        seed.seed_categories(db)
