# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps (build essentials for psycopg-binary not strictly needed, but handy for other libs)
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir "poetry>=1.7,<2.0"

# Copy dependency metadata first (leverage Docker layer caching)
COPY pyproject.toml ./
# If you later add a lockfile, uncomment next line
# COPY poetry.lock* ./

# Install dependencies into the image env (no venv)
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --only main

# Copy project
COPY . .

EXPOSE 8000

# Default command for production; override in compose for dev
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]

