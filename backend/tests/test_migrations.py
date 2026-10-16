"""Alembic migrations build exactly the schema of the models, and upgrade MVP databases."""

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import inspect, text

from app.db import Base, make_engine
from app.migrate import _config, upgrade_to_head


def test_migrations_match_the_models(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'fresh.db'}")
    upgrade_to_head(engine)
    with engine.connect() as connection:
        diff = compare_metadata(MigrationContext.configure(connection), Base.metadata)
    assert diff == []


def test_mvp_database_without_version_table_is_upgraded(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'mvp.db'}")
    with engine.begin() as connection:  # what the MVP left behind: tables but no alembic_version
        command.upgrade(_config(connection), "0001")
        connection.execute(text("DROP TABLE alembic_version"))

    upgrade_to_head(engine)
    columns = {column["name"] for column in inspect(engine).get_columns("workouts")}
    assert "photo_key" in columns
    assert "week_results" in inspect(engine).get_table_names()
