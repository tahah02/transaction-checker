# Docker Commands Reference

## Basic Container Management

### Start Container
```bash
docker-compose up -d
```
- `-d`: Detached mode (background)

### Stop Container
```bash
docker-compose down
```
- Stops and removes containers, networks

### Restart Container
```bash
docker-compose restart
```
- Quick restart without rebuilding

### View Running Containers
```bash
docker ps
```
- Shows all running containers with status

### View All Containers (including stopped)
```bash
docker ps -a
```

## Building & Rebuilding

### Build/Rebuild Container
```bash
docker-compose up -d --build
```
- Rebuilds image if code changes

### Force Rebuild (No Cache)
```bash
docker-compose build --no-cache
docker-compose up -d
```
- Use when changes not reflecting

### Complete Rebuild
```bash
docker-compose down && docker-compose build --no-cache && docker-compose up -d
```
- Full clean rebuild

## Container Interaction

### Enter Container (Bash Shell)
```bash
docker exec -it fraud-detection-api bash
```
- Interactive terminal inside container

### Exit Container
```bash
exit
```

### Run Command Inside Container
```bash
docker exec fraud-detection-api <command>
```

### Examples:
```bash
# List files
docker exec fraud-detection-api ls -la /app/

# Check Python version
docker exec fraud-detection-api python --version

# Check environment variables
docker exec fraud-detection-api env | findstr DB_
```

## Logs & Debugging

### View Container Logs
```bash
docker logs fraud-detection-api
```

### View Last 50 Lines
```bash
docker logs fraud-detection-api --tail 50
```

### Follow Logs (Real-time)
```bash
docker logs fraud-detection-api -f
```

## File Operations

### Copy File to Container
```bash
docker cp <local-file> fraud-detection-api:<container-path>
```

### Example:
```bash
docker cp data\feature_datasetv2.csv fraud-detection-api:/app/data/
```

### Copy File from Container
```bash
docker cp fraud-detection-api:<container-path> <local-path>
```

### Example:
```bash
docker cp fraud-detection-api:/app/backend/model/autoencoder.h5 backend\model\
```

### Create Directory in Container
```bash
docker exec fraud-detection-api mkdir -p /app/data
```

## Training Models

### Train Isolation Forest (Local Machine)
```bash
python -m backend.train_isolation_forest
```

### Train Autoencoder (Inside Container)
```bash
docker exec -it fraud-detection-api bash
python -m backend.train_autoencoder
exit
```

## Health Check

### API Health Endpoint
```bash
curl http://localhost:8000/api/health
```

### Check Container Health
```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

## Cleanup

### Remove All Stopped Containers
```bash
docker container prune
```

### Remove Unused Images
```bash
docker image prune
```

### Remove Everything (Containers, Networks, Images)
```bash
docker system prune -a
```
**Warning:** This removes all unused Docker resources!

## Troubleshooting

### Container Not Starting
```bash
# Check logs
docker logs fraud-detection-api

# Force rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Port Already in Use
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process (replace PID)
taskkill /PID <PID> /F

# Or change port in docker-compose.yml
ports:
  - "8001:8000"
```

### Code Changes Not Reflecting
```bash
# Full rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Database Connection Issues
```bash
# Check environment variables
docker exec fraud-detection-api env | findstr DB_

# Test connection inside container
docker exec -it fraud-detection-api bash
python -c "from backend.db_service import get_db_service; db = get_db_service(); print(db.connect())"
```

## Common Workflows

### Complete Setup from Scratch
```bash
# 1. Build and start
docker-compose up -d --build

# 2. Create data folder
docker exec fraud-detection-api mkdir -p /app/data

# 3. Copy data file
docker cp data\feature_datasetv2.csv fraud-detection-api:/app/data/

# 4. Train models (if needed)
python -m backend.train_isolation_forest

# 5. Check health
curl http://localhost:8000/api/health
```

### Update Code and Restart
```bash
# 1. Stop container
docker-compose down

# 2. Rebuild with changes
docker-compose up -d --build

# 3. Check logs
docker logs fraud-detection-api --tail 50
```

### Quick Restart (No Code Changes)
```bash
docker-compose restart
```

## API Testing

### Test Transaction Endpoint
```bash
curl -X POST http://localhost:8000/api/analyze-transaction \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "1000016",
    "from_account_no": "011000016019",
    "to_account_no": "AE040570000011049381018",
    "transaction_amount": 500.3,
    "transfer_type": "I",
    "datetime": "2025-07-05T16:17:00",
    "bank_country": "UAE"
  }'
```

### Access Swagger UI
```
http://localhost:8000/docs
```

## Notes

- Container name: `fraud-detection-api`
- API Port: `8000`
- Models are synced via volume mount: `./backend/model:/app/backend/model`
- Database credentials are in `docker-compose.yml` environment section
- Use `--no-cache` when code changes don't reflect after rebuild
