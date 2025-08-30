import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# 👇 Add this to include app path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 👇 Import your database and models
from app.database import SQLALCHEMY_DATABASE_URL, Base
from app import models  # Ensure models are imported so Alembic can detect them

# this is the Alembic Config object
config = context.config

# Load .env if using environment variables
from dotenv import load_dotenv
load_dotenv()

# override the sqlalchemy.url from alembic.ini
config.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL)

# Interpret the config file for Python logging.
fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
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
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
