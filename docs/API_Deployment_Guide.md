# Fraud Detection API - Docker Deployment Guide

## Document Information

**Project:** Banking Fraud Detection System  
**Component:** FastAPI REST API  
**Deployment Method:** Docker Containerization  
**Version:** 1.0.0  
**Last Updated:** February 2, 2026  
**Author:** Development Team

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [System Requirements](#system-requirements)
4. [Architecture](#architecture)
5. [Deployment Steps](#deployment-steps)
6. [Configuration](#configuration)
7. [API Endpoints](#api-endpoints)
8. [Monitoring & Health Checks](#monitoring--health-checks)
9. [Troubleshooting](#troubleshooting)
10. [Maintenance](#maintenance)

---

## Overview

This document provides comprehensive instructions for deploying the Fraud Detection API using Docker containers. The API implements a hybrid fraud detection system combining rule-based engines, Isolation Forest, and Autoencoder models.

### Key Features

- Real-time transaction analysis
- Multi-model fraud detection (Rule Engine + ML + Deep Learning)
- Dynamic risk scoring and confidence levels
- Database integration for historical analysis
- RESTful API with FastAPI framework
- Containerized deployment for consistency and scalability

---

## Prerequisites

### Required Software

- **Docker:** Version 20.10 or higher
- **Docker Compose:** Version 2.0 or higher
- **Git:** For repository access

### Required Access

- Database server access (SQL Server)
- Network connectivity to database (Port 1433)
- Host machine with sufficient resources

### Required Files

Ensure the following directory structure exists:

```
project-root/
├── Docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── api/
│   ├── api.py
│   ├── models.py
│   ├── services.py
│   └── helpers.py
├── backend/
│   ├── model/
│   │   ├── isolation_forest.pkl
│   │   ├── isolation_forest_scaler.pkl
│   │   ├── autoencoder.h5
│   │   ├── autoencoder_scaler.pkl
│   │   └── autoencoder_threshold.json
│   ├── config/
│   │   └── risk_thresholds.json
│   └── [other backend files]
├── data/
│   └── api_transactions.csv
└── requirements_api.txt
```

---

## System Requirements

### Minimum Requirements

- **CPU:** 2 cores
- **RAM:** 2 GB
- **Storage:** 5 GB free space
- **OS:** Linux, Windows, or macOS with Docker support

### Recommended Requirements

- **CPU:** 6 cores
- **RAM:** 8 GB
- **Storage:** 20 GB free space
- **Network:** Stable connection to database server

### Resource Allocation

The deployment is configured with the following resource limits:

```yaml
Limits:
  - CPU: 6 cores maximum
  - Memory: 8 GB maximum

Reservations:
  - CPU: 2 cores minimum
  - Memory: 2 GB minimum
```

---

## Architecture

### Container Architecture

```
┌─────────────────────────────────────────────┐
│         Host Machine                        │
│                                             │
│  ┌───────────────────────────────────────┐ │
│  │  Docker Container                     │ │
│  │  (fraud-detection-api)                │ │
│  │                                       │ │
│  │  ┌─────────────────────────────────┐ │ │
│  │  │  FastAPI Application            │ │ │
│  │  │  - API Endpoints                │ │ │
│  │  │  - Request Validation           │ │ │
│  │  │  - Response Formatting          │ │ │
│  │  └─────────────────────────────────┘ │ │
│  │                                       │ │
│  │  ┌─────────────────────────────────┐ │ │
│  │  │  Fraud Detection Engine         │ │ │
│  │  │  - Rule Engine                  │ │ │
│  │  │  - Isolation Forest             │ │ │
│  │  │  - Autoencoder                  │ │ │
│  │  └─────────────────────────────────┘ │ │
│  │                                       │ │
│  │  ┌─────────────────────────────────┐ │ │
│  │  │  Volume Mounts                  │ │ │
│  │  │  - /app/backend/model (models)  │ │ │
│  │  │  - /app/data (transactions)     │ │ │
│  │  └─────────────────────────────────┘ │ │
│  └───────────────────────────────────────┘ │
│                                             │
│  Port Mapping: 8000:8000                   │
└─────────────────────────────────────────────┘
         │
         │ Network Connection
         ▼
┌─────────────────────────────────────────────┐
│     SQL Server Database                     │
│     (10.112.32.4:1433)                      │
└─────────────────────────────────────────────┘
```

### Technology Stack

- **Framework:** FastAPI 0.104.1
- **Server:** Uvicorn 0.24.0
- **ML Libraries:** scikit-learn 1.7.2, TensorFlow 2.15.0
- **Database Driver:** pymssql 2.2.11
- **Base Image:** Python 3.10-slim

---

## Deployment Steps

### Step 1: Prepare Environment

Navigate to the Docker directory:

```bash
cd Docker
```

### Step 2: Configure Environment Variables

Review and update database credentials in `docker-compose.yml`:

```yaml
environment:
  - DB_SERVER=10.112.32.4
  - DB_PORT=1433
  - DB_DATABASE=retailchannelLogs
  - DB_USERNAME=dbuser
  - DB_PASSWORD=Codebase202212?!
```

**Security Note:** For production, use Docker secrets or environment files instead of hardcoded credentials.

### Step 3: Build Docker Image

Build the container image:

```bash
docker-compose build --no-cache
```

**Expected Output:**
```
Building fraud-detection-api
Step 1/10 : FROM python:3.10-slim
...
Successfully built [image-id]
Successfully tagged fraud-detection-api:latest
```

**Build Time:** Approximately 5-10 minutes (first build)

### Step 4: Start Container

Launch the container in detached mode:

```bash
docker-compose up -d
```

**Expected Output:**
```
Creating network "fraud-net" with driver "bridge"
Creating fraud-detection-api ... done
```

### Step 5: Verify Deployment

Check container status:

```bash
docker-compose ps
```

**Expected Output:**
```
NAME                    STATUS              PORTS
fraud-detection-api     Up 30 seconds       0.0.0.0:8000->8000/tcp
```

### Step 6: View Logs

Monitor application logs:

```bash
docker-compose logs -f fraud-detection-api
```

**Expected Output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 7: Test Health Endpoint

Verify API is responding:

```bash
curl http://localhost:8000/api/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-02T14:30:00",
  "models": {
    "isolation_forest": "loaded",
    "autoencoder": "loaded"
  },
  "database": {
    "status": "connected"
  }
}
```

---

## Configuration

### Database Configuration

Update database connection parameters in `docker-compose.yml`:

```yaml
environment:
  - DB_SERVER=<your-db-server>
  - DB_PORT=<your-db-port>
  - DB_DATABASE=<your-database>
  - DB_USERNAME=<your-username>
  - DB_PASSWORD=<your-password>
```

### Risk Thresholds Configuration

Risk thresholds are configured in `backend/config/risk_thresholds.json`:

```json
{
  "isolation_forest": {
    "high_risk_threshold": 0.7,
    "medium_risk_threshold": 0.5,
    "low_risk_threshold": 0.3
  },
  "confidence_calculation": {
    "all_models_agree": 0.95,
    "two_models_agree": 0.80,
    "one_model_agrees": 0.60,
    "high_risk_boost": 0.03
  }
}
```

**Note:** Changes to this file require container restart.

### Volume Mounts

The following directories are mounted from host to container:

```yaml
volumes:
  - ../backend/model:/app/backend/model    # ML models
  - ../data:/app/data                      # Transaction data
```

**Benefits:**
- Model updates without rebuilding image
- Persistent transaction logs
- Easy backup and recovery

### Port Configuration

Default port mapping:

```yaml
ports:
  - "8000:8000"
```

To change the external port:

```yaml
ports:
  - "9000:8000"  # Access via http://localhost:9000
```

---

## API Endpoints

### 1. Health Check

**Endpoint:** `GET /api/health`

**Purpose:** Verify API and dependencies status

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-02T14:30:00",
  "models": {
    "isolation_forest": "loaded",
    "autoencoder": "loaded"
  },
  "database": {
    "status": "connected"
  }
}
```

### 2. Analyze Transaction

**Endpoint:** `POST /api/analyze-transaction`

**Purpose:** Analyze transaction for fraud detection

**Request Body:**
```json
{
  "customer_id": "CUST001",
  "from_account_no": "ACC123456",
  "to_account_no": "ACC789012",
  "transaction_amount": 15000,
  "transfer_type": "S",
  "datetime": "2026-02-02T14:30:00",
  "bank_country": "UAE"
}
```

**Response:**
```json
{
  "decision": "REQUIRES_USER_APPROVAL",
  "risk_score": 0.65,
  "risk_level": "MEDIUM",
  "confidence_level": 0.80,
  "model_agreement": 0.67,
  "reasons": [
    "Velocity limit exceeded: 6 transactions in last 10 minutes",
    "ML anomaly detected: abnormal behavior pattern"
  ],
  "individual_scores": {
    "rule_engine": {
      "violated": true,
      "threshold": 9000.0
    },
    "isolation_forest": {
      "anomaly_score": 0.65,
      "is_anomaly": true
    },
    "autoencoder": {
      "reconstruction_error": 0.20,
      "is_anomaly": false
    }
  },
  "transaction_id": "txn_a1fa1c17",
  "processing_time_ms": 579
}
```

### 3. Approve Transaction

**Endpoint:** `POST /api/transaction/approve`

**Request Body:**
```json
{
  "transaction_id": "txn_a1fa1c17",
  "customer_id": "CUST001",
  "comments": "Verified with customer"
}
```

### 4. Reject Transaction

**Endpoint:** `POST /api/transaction/reject`

**Request Body:**
```json
{
  "transaction_id": "txn_a1fa1c17",
  "customer_id": "CUST001",
  "reason": "Suspicious activity detected"
}
```

### 5. List Pending Transactions

**Endpoint:** `GET /api/transactions/pending`

**Response:** List of transactions requiring approval

---

## Monitoring & Health Checks

### Built-in Health Check

Docker automatically monitors container health:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3
```

**Parameters:**
- **Interval:** Check every 30 seconds
- **Timeout:** 10 seconds per check
- **Start Period:** Wait 40 seconds before first check
- **Retries:** 3 failed checks before marking unhealthy

### Manual Health Check

```bash
docker exec fraud-detection-api curl http://localhost:8000/api/health
```

### Container Logs

View real-time logs:

```bash
docker-compose logs -f fraud-detection-api
```

View last 100 lines:

```bash
docker-compose logs --tail=100 fraud-detection-api
```

### Resource Monitoring

Check container resource usage:

```bash
docker stats fraud-detection-api
```

**Output:**
```
CONTAINER ID   NAME                    CPU %   MEM USAGE / LIMIT   NET I/O
abc123def456   fraud-detection-api     15.2%   1.2GiB / 8GiB      1.5MB / 2.3MB
```

---

## Troubleshooting

### Issue 1: Container Fails to Start

**Symptoms:**
```bash
docker-compose ps
# Shows: Exit 1
```

**Solution:**
```bash
docker-compose logs fraud-detection-api
```

Check for:
- Missing model files
- Database connection errors
- Port conflicts

### Issue 2: Database Connection Failed

**Symptoms:**
```json
{
  "database": {
    "status": "connection_failed"
  }
}
```

**Solutions:**
1. Verify database server is accessible:
   ```bash
   telnet 10.112.32.4 1433
   ```

2. Check credentials in `docker-compose.yml`

3. Verify network connectivity from container:
   ```bash
   docker exec fraud-detection-api ping 10.112.32.4
   ```

### Issue 3: Models Not Loading

**Symptoms:**
```json
{
  "models": {
    "isolation_forest": "unavailable"
  }
}
```

**Solutions:**
1. Verify model files exist:
   ```bash
   ls -la backend/model/
   ```

2. Check volume mounts:
   ```bash
   docker exec fraud-detection-api ls -la /app/backend/model/
   ```

3. Rebuild container:
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

### Issue 4: Port Already in Use

**Symptoms:**
```
Error: bind: address already in use
```

**Solutions:**
1. Check what's using port 8000:
   ```bash
   netstat -ano | findstr :8000
   ```

2. Change port in `docker-compose.yml`:
   ```yaml
   ports:
     - "9000:8000"
   ```

### Issue 5: High Memory Usage

**Symptoms:**
Container using >6GB RAM

**Solutions:**
1. Reduce worker count in Dockerfile:
   ```dockerfile
   CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
   ```

2. Adjust memory limits in `docker-compose.yml`:
   ```yaml
   deploy:
     resources:
       limits:
         memory: 4G
   ```

---

## Maintenance

### Updating the Application

1. Stop the container:
   ```bash
   docker-compose down
   ```

2. Pull latest code:
   ```bash
   git pull origin main
   ```

3. Rebuild and restart:
   ```bash
   docker-compose build --no-cache
   docker-compose up -d
   ```

### Updating Models

Models are mounted as volumes, so updates don't require rebuild:

1. Replace model files in `backend/model/`
2. Restart container:
   ```bash
   docker-compose restart fraud-detection-api
   ```

### Backup Procedures

**Backup Models:**
```bash
tar -czf models-backup-$(date +%Y%m%d).tar.gz backend/model/
```

**Backup Transaction Data:**
```bash
tar -czf data-backup-$(date +%Y%m%d).tar.gz data/
```

**Backup Configuration:**
```bash
tar -czf config-backup-$(date +%Y%m%d).tar.gz backend/config/
```

### Log Rotation

Container logs can grow large. Rotate logs:

```bash
docker-compose logs --tail=1000 fraud-detection-api > logs-$(date +%Y%m%d).txt
docker-compose restart fraud-detection-api
```

### Cleanup

Remove stopped containers and unused images:

```bash
docker system prune -a
```

**Warning:** This removes all unused Docker resources.

---

## Performance Optimization

### Recommended Settings

For production environments:

1. **Enable multiple workers** (if sufficient RAM):
   ```dockerfile
   CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
   ```

2. **Increase resource limits**:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '8'
         memory: 16G
   ```

3. **Enable logging to file**:
   ```yaml
   volumes:
     - ./logs:/app/logs
   ```

### Performance Metrics

Expected performance:
- **Response Time:** 200-600ms per transaction
- **Throughput:** 50-100 requests/second (single worker)
- **Memory Usage:** 1-2GB (single worker)
- **CPU Usage:** 10-30% (idle), 50-80% (under load)

---

## Security Considerations

### Production Recommendations

1. **Use environment files** instead of hardcoded credentials:
   ```bash
   docker-compose --env-file .env.production up -d
   ```

2. **Enable HTTPS** with reverse proxy (nginx/traefik)

3. **Implement rate limiting** at API gateway level

4. **Regular security updates**:
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

5. **Network isolation**:
   ```yaml
   networks:
     fraud-net:
       driver: bridge
       internal: true
   ```

---

## Support & Contact

For issues or questions:

- **Technical Lead:** [Your Name]
- **Email:** [your.email@company.com]
- **Documentation:** `/docs` directory
- **API Documentation:** `http://localhost:8000/docs` (Swagger UI)

---

## Appendix

### A. Complete docker-compose.yml

```yaml
version: '3.8'

services:
  fraud-detection-api:
    build:
      context: ..
      dockerfile: Docker/Dockerfile
    container_name: fraud-detection-api
    ports:
      - "8000:8000"
    environment:
      - DB_SERVER=10.112.32.4
      - DB_PORT=1433
      - DB_DATABASE=retailchannelLogs
      - DB_USERNAME=dbuser
      - DB_PASSWORD=Codebase202212?!
      - PYTHONUNBUFFERED=1
    volumes:
      - ../backend/model:/app/backend/model
      - ../data:/app/data
    restart: unless-stopped
    networks:
      - fraud-net
    deploy:
      resources:
        limits:
          cpus: '6'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 2G

networks:
  fraud-net:
    driver: bridge
```

### B. Quick Reference Commands

```bash
# Build
docker-compose build --no-cache

# Start
docker-compose up -d

# Stop
docker-compose down

# Restart
docker-compose restart

# Logs
docker-compose logs -f

# Status
docker-compose ps

# Execute command in container
docker exec -it fraud-detection-api bash

# Health check
curl http://localhost:8000/api/health
```

---

**Document Version:** 1.0.0  
**Last Review Date:** February 2, 2026  
**Next Review Date:** May 2, 2026
