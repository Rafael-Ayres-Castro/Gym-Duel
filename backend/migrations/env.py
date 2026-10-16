"""Alembic environment: migrations run against the app's own engine (see app/migrate.py).

`render_as_batch` lets SQLite alter tables (it has almost no ALTER TABLE support).
"""

from alembic import context

from app.db import Base
from app import models  # noqa: F401  (registers every table on Base.metadata)

connection = context.config.attributes["connection"]
context.configure(connection=connection, target_metadata=Base.metadata, render_as_batch=True)

with context.begin_transaction():
    context.run_migrations()
