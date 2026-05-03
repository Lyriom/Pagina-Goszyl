# syntax=docker/dockerfile:1.7
# =====================================================================
# Sistema A - Dockerfile multi-stage para produccion
# Stage 1 (builder): instala dependencias en una venv aislada.
# Stage 2 (runtime): imagen final minima, sin toolchain de compilacion.
# =====================================================================

# ---------- Stage 1: builder ----------
FROM python:3.11-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Dependencias de compilacion para asyncpg / cryptography
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Crear venv aislada para copiarla luego al runtime
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt


# ---------- Stage 2: runtime ----------
FROM python:3.11-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:${PATH}" \
    PORT=8000

# Solo libpq runtime (no compilador) para reducir superficie
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system app \
    && useradd  --system --gid app --home /app --shell /usr/sbin/nologin app

WORKDIR /app

# Copiar la venv ya construida
COPY --from=builder /opt/venv /opt/venv

# Copiar el codigo
COPY --chown=app:app . /app

USER app

EXPOSE 8000

# Healthcheck simple contra la ruta publica /healthz
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD curl -fsS http://localhost:${PORT}/healthz || exit 1

# Gunicorn + UvicornWorker para produccion
CMD ["gunicorn", "app.main:app", \
     "--workers", "3", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--forwarded-allow-ips", "*"]
