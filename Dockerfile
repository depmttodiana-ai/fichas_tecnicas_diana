# ── Etapa 1: Build ─────────────────────────────────
FROM python:3.13-slim AS builder

WORKDIR /build

# Instalar uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copiar archivos de dependencias
COPY pyproject.toml uv.lock ./

# Instalar dependencias
RUN uv sync --frozen --no-dev

# ── Etapa 2: Runtime ──────────────────────────────
FROM python:3.13-slim AS runtime

WORKDIR /app

# Instalar dependencias del sistema para psycopg
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependencias instaladas desde builder
COPY --from=builder /build/.venv /app/.venv

# Asegurar que el PATH use el venv
ENV PATH="/app/.venv/bin:$PATH"

# Copiar código fuente
COPY alembic/ alembic/
COPY alembic.ini .
COPY app/ app/

# Crear directorio de uploads (por si se usa storage local)
RUN mkdir -p uploads

# Puerto
EXPOSE 8000

# Comando por defecto
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
