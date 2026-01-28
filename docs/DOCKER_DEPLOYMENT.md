# 🐳 Docker Deployment Guide - Fraud Detection API

## 📋 Prerequisites

- Docker installed (version 20.10+)
- Docker Compose installed (version 1.29+)
- Models present in `backend/model/` folder
- Network access to SQL Server (10.112.32.4:1433)

---

## 🚀 Quick Start

### Step 1: Build the Docker Image

```bash
docker-compose build
```

**Expected Output:**
```
Building fraud-detection-api
Step 1/10 : FROM python:3.10-slim
...
Successfully built abc123def456
Successfully tagged fraud-detection-api:latest
```

**Build Time:** 5-7 minutes (first time)  
**Image Size:** ~700 MB (without models)

---

### Step 2: Start the Container

```bash
docker-compose up -d
```

**Expected Output:**
```
Creating network "fraud-net" with driver "bridge"
Creating fraud-detection-api ... done
```

---

### Step 3: Verify Container is Running

```bash
docker ps
```

**Expected Output:**
```
CONTAINER ID   IMAGE                    STATUS         PORTS
abc123def456   fraud-detection-api      Up 10 seconds  0.0.0.0:8000->8000/tcp
```

---

### Step 4: Check Health Status

```bash
curl http://localhost:8000/api/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-28T10:00:00",
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

## 🧪 Testing the API

### Test Transaction Analysis

```bash
curl -X POST http://localhost:8000/api/analyze-transaction \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "1019321",
    "from_account_no": "011019321016",
    "to_account_no": "AE470030010010409920001",
    "transaction_amount": 5000,
    "transfer_type": "L",
    "datetime": "2025-01-28T10:00:00",
    "bank_country": "UAE"
  }'
```

**Expected Response:**
```json
{
  "decision": "APPROVED",
  "risk_score": 0.234,
  "confidence_level": 0.85,
  "reasons": [],
  "individual_scores": {...},
  "transaction_id": "txn_abc12345",
  "processing_time_ms": 45
}
```

---

## 📊 Container Management

### View Logs

```bash
# Real-time logs
docker-compose logs -f

# Last 100 lines
docker logs --tail 100 fraud-detection-api

# Logs with timestamps
docker logs -t fraud-detection-api
```

### Stop Container

```bash
docker-compose down
```

### Restart Container

```bash
docker-compose restart
```

### Remove Everything (including volumes)

```bash
docker-compose down -v
```

---

## 🔧 Model Updates

### Update Models WITHOUT Rebuilding Container

Since models are mounted via volume, you can update them easily:

```bash
# Step 1: Stop container
docker-compose down

# Step 2: Replace model files
cp new_autoencoder.h5 backend/model/autoencoder.h5
cp new_isolation_forest.pkl backend/model/isolation_forest.pkl

# Step 3: Start container
docker-compose up -d

# Models are automatically loaded!
```

**No rebuild needed!** ✅

---

## 🐛 Troubleshooting

### Issue 1: Container Won't Start

```bash
# Check logs
docker logs fraud-detection-api

# Common causes:
# - Port 8000 already in use
# - Models not found
# - Database connection failed
```

**Solution:**
```bash
# Change port in docker-compose.yml
ports:
  - "8001:8000"  # Use different port
```

---

### Issue 2: Database Connection Failed

```bash
# Test network connectivity
docker exec fraud-detection-api ping 10.112.32.4

# Check database credentials
docker exec fraud-detection-api env | grep DB_
```

**Solution:**
- Verify SQL Server is accessible from Docker network
- Check firewall rules
- Verify credentials in docker-compose.yml

---

### Issue 3: Models Not Loading

```bash
# Check if models are mounted
docker exec fraud-detection-api ls -la /app/backend/model/

# Expected output:
# autoencoder.h5
# autoencoder_scaler.pkl
# autoencoder_threshold.json
# isolation_forest.pkl
# isolation_forest_scaler.pkl
```

**Solution:**
```bash
# Ensure models exist on host
ls -la backend/model/

# Check volume mount in docker-compose.yml
```

---

### Issue 4: High Memory Usage

```bash
# Check resource usage
docker stats fraud-detection-api
```

**Solution:**
```yaml
# Adjust limits in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G  # Increase if needed
```

---

## 🌐 Production Deployment

### Option 1: Deploy on Cloud Server

```bash
# SSH to server
ssh user@your-server.com

# Clone repository
git clone <your-repo>
cd <project-folder>

# Start container
docker-compose up -d

# Access API
curl http://your-server.com:8000/api/health
```

---

### Option 2: Deploy on AWS ECS

```bash
# Build and tag image
docker build -t fraud-detection-api:v1 .

# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker tag fraud-detection-api:v1 <account-id>.dkr.ecr.us-east-1.amazonaws.com/fraud-api:v1
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/fraud-api:v1

# Deploy to ECS (use AWS Console or CLI)
```

---

### Option 3: Deploy on Azure Container Instances

```bash
# Login to Azure
az login

# Create container
az container create \
  --resource-group myResourceGroup \
  --name fraud-detection-api \
  --image fraud-detection-api:latest \
  --ports 8000 \
  --environment-variables \
    DB_SERVER=10.112.32.4 \
    DB_PORT=1433 \
    DB_DATABASE=retailchannelLogs \
    DB_USERNAME=dbuser \
    DB_PASSWORD=Codebase202212?!
```

---

## 📈 Monitoring

### Health Check Endpoint

```bash
# Check every 30 seconds
watch -n 30 'curl -s http://localhost:8000/api/health | jq'
```

### Resource Monitoring

```bash
# Real-time stats
docker stats fraud-detection-api

# Output:
# CONTAINER ID   CPU %   MEM USAGE / LIMIT   MEM %   NET I/O
# abc123def456   5.2%    512MB / 2GB         25.6%   1.2MB / 850KB
```

---

## 🔐 Security Best Practices

### 1. Use Environment Variables for Secrets

```yaml
# docker-compose.yml
environment:
  - DB_PASSWORD=${DB_PASSWORD}  # From .env file
```

```bash
# .env file (don't commit to git!)
DB_PASSWORD=your_secure_password
```

### 2. Run as Non-Root User

```dockerfile
# Add to Dockerfile
RUN useradd -m -u 1000 appuser
USER appuser
```

### 3. Use Read-Only Volumes

```yaml
volumes:
  - ./backend/model:/app/backend/model:ro  # :ro = read-only
```

---

## 📦 Image Size Optimization

### Current Setup:
- **Base Image:** python:3.10-slim (~150 MB)
- **Dependencies:** ~500 MB
- **Application Code:** ~50 MB
- **Total:** ~700 MB (without models)

### With Models Mounted:
- Models stay on host (~50 MB)
- Container image: 700 MB
- **Total deployment:** 750 MB

### Alternative (Models Inside):
- Container image: 1.2 GB
- Less flexible for updates

---

## 🎯 Performance Tuning

### Increase Workers (for high traffic)

```yaml
# docker-compose.yml
command: ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Enable GPU Support (if available)

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

---

## 📞 Support

For issues or questions:
1. Check logs: `docker logs fraud-detection-api`
2. Verify health: `curl http://localhost:8000/api/health`
3. Review this guide
4. Contact DevOps team

---

## ✅ Checklist

Before deployment:
- [ ] Docker and Docker Compose installed
- [ ] Models present in `backend/model/`
- [ ] Database accessible from Docker network
- [ ] Port 8000 available
- [ ] Environment variables configured
- [ ] `.dockerignore` file present
- [ ] Tested locally with `docker-compose up`

---

**Last Updated:** January 28, 2025  
**Version:** 1.0.0
