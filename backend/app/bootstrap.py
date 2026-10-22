"""Container start-up: run migrations, then load the data if the database is empty.

app.seed drops every table, so it can't run on each boot against a real database.
"""
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from .database import engine, SessionLocal
from .models import Author
from . import seed, seed_demo

BASE_DIR = Path(__file__).resolve().parent.parent


def migrate() -> None:
    cfg = Config(str(BASE_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BASE_DIR / "alembic"))
    tables = inspect(engine).get_table_names()
    if "authors" in tables and "alembic_version" not in tables:
        # created before migrations existed, schema already matches the first revision
        command.stamp(cfg, "head")
    else:
        command.upgrade(cfg, "head")


def run() -> None:
    migrate()
    db = SessionLocal()
    try:
        empty = db.query(Author).count() == 0
    finally:
        db.close()
    if empty:
        seed.run()
        seed_demo.run()
    else:
        print("db already has data, skipping seed")


if __name__ == "__main__":
    run()
