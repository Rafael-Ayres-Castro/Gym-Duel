"""Brings the database schema up to date with Alembic when the app starts.

Databases created by the MVP (before Alembic) already have the first tables but no
version table: they are stamped at revision 0001 and then upgraded normally.
"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.engine import Engine

MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations"
MVP_REVISION = "0001"


def _config(connection) -> Config:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.attributes["connection"] = connection
    return config


def upgrade_to_head(engine: Engine) -> None:
    with engine.begin() as connection:
        tables = set(inspect(connection).get_table_names())
        config = _config(connection)
        if "users" in tables and "alembic_version" not in tables:
            command.stamp(config, MVP_REVISION)
        command.upgrade(config, "head")
