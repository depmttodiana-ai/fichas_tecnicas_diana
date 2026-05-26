from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

from sqlmodel import SQLModel

# ── Importar TODOS los modelos para que Alembic los detecte ──
from app.models import (
    Usuario,
    Area,
    ClasificacionEquipo,
    Equipo,
    Foto,
    Mantenimiento,
    MantenimientoRepuesto,
    HistorialCambio,
)
from app.models.equipo_repuesto import EquipoRepuesto

from app.core.config import settings

# this is the Alembic Config object
config = context.config

# Configurar la URL de la BD desde settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# MetaData para autogenerate
target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
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


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
