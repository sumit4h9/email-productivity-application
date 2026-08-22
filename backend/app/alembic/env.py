import os
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

import app.models.attachment  # noqa: F401 (ensure models are imported)
import app.models.connected_account  # noqa: F401 (ensure models are imported)
import app.models.email  # noqa: F401 (ensure models are imported)
import app.models.password_reset_token  # noqa: F401 (ensure models are imported)
import app.models.session  # noqa: F401 (ensure models are imported)
import app.models.user  # noqa: F401 (ensure models are imported)
import app.models.user_session  # noqa: F401 (ensure models are imported)
import app.models.verification_code  # noqa: F401 (ensure models are imported)

# Import your metadata
from app.db.base import Base  # declarative Base

# Load .env
load_dotenv()

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Point Alembic at your DB URL from env
db_url = os.getenv("DATABASE_URL")
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)

    db_url = db_url.strip()

print(">>> Using DATABASE_URL:", repr(db_url))

target_metadata = Base.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
