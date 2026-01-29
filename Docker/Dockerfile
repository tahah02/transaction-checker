FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies for pymssql
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    freetds-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements_api.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements_api.txt && \
    pip install --no-cache-dir pymssql==2.2.11

# Copy application code (excluding models - they will be mounted)
COPY api/ ./api/
COPY backend/ ./backend/

# Note: Models will be mounted from host via volume
# This keeps the image size smaller and allows easy model updates

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/health')" || exit 1

# Run FastAPI with uvicorn
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
