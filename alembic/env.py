from logging.config import fileConfig
import os
import logging
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from app.core.config import get_settings
from app.models.base import Base

# Configure logging
logger = logging.getLogger("alembic.env")

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Get database URL from environment or settings
database_url = os.getenv("DATABASE_URL")
logger.info("Configuring database connection...")

if database_url and database_url.startswith("postgres://"):
    logger.info("Converting postgres:// to postgresql:// in database URL")
    database_url = database_url.replace("postgres://", "postgresql://", 1)

if not database_url:
    logger.info("No DATABASE_URL in environment, getting from settings")
    settings = get_settings()
    database_url = settings.DATABASE_URL

logger.info(f"Using database host: {database_url.split('@')[-1] if '@' in database_url else 'configured'}")
config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    logger.info("Running offline migrations")
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()
    logger.info("Offline migrations completed")


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    logger.info("Setting up async database connection")
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        logger.info("Running migrations")
        await connection.run_sync(do_run_migrations)
        logger.info("Migrations completed successfully")

    await connectable.dispose()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    logger.info("Starting online migrations")
    from asyncio import run
    run(run_async_migrations())
    logger.info("Online migrations completed")


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
