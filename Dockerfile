# syntax=docker/dockerfile:1

# ========================================
# Stage 1: Base runtime mínima
# ========================================
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /code

# ========================================
# Stage 2: Dependencies Builder
# ========================================
FROM base AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Crear entorno virtual aislado
RUN python -m venv /opt/venv

COPY requirements.txt .

# Usar caché de BuildKit (no ocupa espacio en la imagen final, pero acelera builds)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install -r requirements.txt

# ========================================
# Stage 3: Development (para docker compose watch)
# ========================================
FROM base AS development

COPY --from=builder /opt/venv /opt/venv

RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser && \
    mkdir -p /code/logs && \
    chown -R appuser:appuser /code

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ========================================
# Stage 4: Production (Optimizado para Render / ECS)
# ========================================
FROM base AS production

# Copiar únicamente el entorno virtual compilado
COPY --from=builder /opt/venv /opt/venv

RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser && \
    mkdir -p /code/logs && \
    chown -R appuser:appuser /code

# Copiar código fuente (asegúrate de excluir .env, tests y .git en .dockerignore)
COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

# Healthcheck nativo en Python (sin necesidad de instalar curl)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

LABEL maintainer="qolqa-team" \
      app.name="qolqa-backend" \
      app.version="1.0.0" \
      app.description="QOLQA Backend API"

# Usar shell form o variable ${PORT:-8000} para compatibilidad total con Render y ECS
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2 --log-level info --access-log --proxy-headers --forwarded-allow-ips '*'"]
