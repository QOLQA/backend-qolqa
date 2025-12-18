# ========================================
# Multi-stage Dockerfile optimized for AWS ECS/Fargate
# ========================================

# ========================================
# Stage 1: Base - Common dependencies
# ========================================
FROM python:3.12-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
	PYTHONDONTWRITEBYTECODE=1 \
	PIP_NO_CACHE_DIR=1 \
	PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /code

# Install system dependencies with specific versions for reproducibility
# Only essential packages to keep image small
RUN apt-get update && apt-get install -y --no-install-recommends \
	curl \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/* \
	&& rm -rf /tmp/* /var/tmp/*

# ========================================
# Stage 2: Dependencies Builder
# ========================================
FROM base AS builder

# Install build dependencies (only needed during build)
RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential=12.* \
	gcc=4:* \
	&& rm -rf /var/lib/apt/lists/*

# Copy only requirements first (better layer caching)
COPY requirements.txt .

# Install Python dependencies
# Use --no-cache-dir to reduce image size
RUN pip install --upgrade pip==24.* && \
	pip install --no-cache-dir -r requirements.txt

# ========================================
# Stage 3: Development (for docker-compose)
# ========================================
FROM base AS development

# Copy dependencies from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
	chown -R appuser:appuser /code && \
	mkdir -p /code/logs && \
	chown -R appuser:appuser /code/logs

USER appuser

EXPOSE 8000

# Development command with hot-reload
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ========================================
# Stage 4: Production (for AWS ECS)
# ========================================
FROM base AS production

# Copy only runtime dependencies (not build tools)
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create non-root user and necessary directories
RUN groupadd -r appuser && \
	useradd -r -g appuser -u 1000 appuser && \
	mkdir -p /code/logs && \
	chown -R appuser:appuser /code

# Set working directory
WORKDIR /code

# Copy application code (respects .dockerignore)
# This is separate from deps for better caching
COPY --chown=appuser:appuser . .

# Remove any accidentally copied sensitive files as extra safety
RUN rm -f .env .env.* || true && \
	rm -rf tests/ __pycache__/ .pytest_cache/ || true && \
	rm -rf .git/ .github/ || true

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Healthcheck for AWS ECS
# ECS will use this to determine if container is healthy
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
	CMD curl -f http://localhost:8000/health || exit 1

# Labels for better container management
LABEL maintainer="qolqa-team" \
	app.name="qolqa-backend" \
	app.version="1.0.0" \
	app.description="QOLQA Backend API"

# Production command with multiple workers
# Workers calculated based on CPU: (2 × CPU cores) + 1
# For Fargate 0.5 vCPU: 2 workers
# For Fargate 1 vCPU: 3 workers
# Override in ECS task definition for larger instances
CMD ["uvicorn", "main:app", \
	"--host", "0.0.0.0", \
	"--port", "8000", \
	"--workers", "2", \
	"--log-level", "info", \
	"--access-log", \
	"--proxy-headers", \
	"--forwarded-allow-ips", "*"]