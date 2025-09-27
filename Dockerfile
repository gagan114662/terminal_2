# Multi-stage build for secure Python API
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY requirements*.txt ./
COPY auth_requirements.txt ./
COPY blog_requirements.txt ./
COPY todo_requirements.txt ./
COPY requirements_flask.txt ./

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt || true && \
    pip install --no-cache-dir -r requirements-dev.txt || true && \
    pip install --no-cache-dir -r auth_requirements.txt || true && \
    pip install --no-cache-dir -r blog_requirements.txt || true && \
    pip install --no-cache-dir -r todo_requirements.txt || true && \
    pip install --no-cache-dir -r requirements_flask.txt || true && \
    pip install --no-cache-dir flask flask-cors flask-sqlalchemy flask-jwt-extended python-dotenv

# Final stage - minimal runtime image
FROM python:3.11-slim

# Security: Run as non-root user
RUN useradd -m -u 1000 apiuser && \
    mkdir -p /app/instance /app/static /app/templates /app/termnet && \
    chown -R apiuser:apiuser /app

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder --chown=apiuser:apiuser /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=apiuser:apiuser . .

# Security: Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=auth_api.py \
    FLASK_ENV=production

# Create volume mount points
VOLUME ["/app/instance", "/app/logs"]

# Switch to non-root user
USER apiuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# Expose port
EXPOSE 5000

# Start application
CMD ["python", "auth_api.py"]
