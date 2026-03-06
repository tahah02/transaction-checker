FROM python:3.10-windowsservercore-1809
# Set working directory
WORKDIR C:\app

# Install system dependencies for pymssql
RUN powershell -Command \
    choco install -y python --version=3.10.0 ; \
    choco install -y visualstudio2019-workload-vctools ; \
    choco install -y freetds

# Refresh PATH
RUN powershell -Command $env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')

# Copy requirements file
COPY requirements_api.txt .

# Install Python dependencies
RUN powershell -Command \
    pip install --upgrade pip ; \
    pip install --no-cache-dir -r requirements_api.txt ; \
    pip install --no-cache-dir pymssql==2.2.11

# Copy application code (excluding models - they will be mounted)
COPY api\ .\api\
COPY backend\ .\backend\

# Note: Models will be mounted from host via volume
# This keeps the image size smaller and allows easy model updates

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:8000/api/health' -UseBasicParsing; exit 0 } catch { exit 1 }"

# Run FastAPI with uvicorn
ENTRYPOINT ["powershell", "-Command", "uvicorn api:app --host 0.0.0.0 --port 8000 --workers 1"]
