import os

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app import bootstrap
from app.config import settings


def test_migration_creates_the_schema(monkeypatch, tmp_path):
    url = f"sqlite:///{tmp_path / 'm.db'}"
    monkeypatch.setattr(settings, "database_url", url)
    cfg = Config(os.path.join(bootstrap.BASE_DIR, "alembic.ini"))
    cfg.set_main_option("script_location", str(bootstrap.BASE_DIR / "alembic"))
    command.upgrade(cfg, "head")
    tables = set(inspect(create_engine(url)).get_table_names())
    assert {"authors", "books", "admins", "tickets", "ticket_responses", "internal_notes",
            "alembic_version"} <= tables
