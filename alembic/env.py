from logging.config import fileConfig
import os

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from app.core.database import Base


# ---------------------------------------------------------
# Environment / Alembic configuration
# ---------------------------------------------------------

load_dotenv()

config = context.config

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is not configured."
    )


# Explicitly use Psycopg 3 with SQLAlchemy.
#
# Railway provides PostgreSQL URLs beginning with:
# postgresql://
#
# SQLAlchemy's Psycopg 3 dialect uses:
# postgresql+psycopg://
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://",
        "postgresql+psycopg://",
        1,
    )


# Override sqlalchemy.url from alembic.ini with the
# environment-specific database URL.
config.set_main_option(
    "sqlalchemy.url",
    DATABASE_URL,
)


# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# ---------------------------------------------------------
# SQLAlchemy metadata
# ---------------------------------------------------------

target_metadata = Base.metadata


# ---------------------------------------------------------
# Offline migrations
# ---------------------------------------------------------

def run_migrations_offline() -> None:

    url = config.get_main_option(
        "sqlalchemy.url"
    )

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named"
        },
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------
# Online migrations
# ---------------------------------------------------------

def run_migrations_online() -> None:

    connectable = engine_from_config(
        config.get_section(
            config.config_ini_section,
            {}
        ),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


# ---------------------------------------------------------
# Execute
# ---------------------------------------------------------

if context.is_offline_mode():
    run_migrations_offline()

else:
    run_migrations_online()