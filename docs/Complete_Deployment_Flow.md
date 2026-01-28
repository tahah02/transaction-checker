# Complete Deployment Flow - Fraud Detection API

## Overview
This document explains the complete flow from development to Docker deployment and transaction processing.

---

## 1. Development Setup

### Local Environment
```
Project Structure:
├── backend/
│   ├── model/              # Trained ML models
│   ├── db_service.py       # Database operations
│   ├── rule_engine.py      # Business rules
│   ├── hybrid_decision.py  # Decision logic
│   └── train_*.py          # Training scripts
├── docker/
│   ├── Dockerfile          # Container image definition
│   ├── docker-compose.yml  # Container orchestration
│   └── .dockerignore       # Files to exclude
├── data/
│   └── feature_datasetv2.csv  # Training data
└── api.py                  # FastAPI application
```

### Prerequisites
- Python 3.10+
- Docker Desktop
- SQL Server Database
- scikit-learn 1.7.2
- TensorFlow 2.15.0

---

## 2. Model Training Flow

### Step 1: Prepare Data
```bash
# Data location
data/feature_datasetv2.csv (3502 transactions)
```

### Step 2: Train Isolation Forest (Local Machine)
```bash
python -m backend.train_isolation_forest
```

**What Happens:**
1. Loads CSV data
2. Extracts features (amount, velocity, user stats, etc.)
3. Normalizes data using StandardScaler
4. Trains Isolation Forest model (contamination=5%)
5. Validates model performance
6. Saves files:
   - `backend/model/isolation_forest.pkl` (model + metadata)
   - `backend/model/isolation_forest_scaler.pkl` (scaler)

**Output:**
```
Training done | Anomalies detected: 176/3502 (5.03%)
Model validation PASSED
```

### Step 3: Train Autoencoder (Container)
```bash
docker exec -it fraud-detection-api bash
python -m backend.train_autoencoder
exit
```

**What Happens:**
1. Loads CSV data
2. Normalizes data using StandardScaler
3. Builds neural network (encoder-decoder architecture)
4. Trains for 100 epochs (with early stopping)
5. Stops at epoch 89 due to early stopping (no improvement in loss)
6. Calculates reconstruction error threshold (95th percentile)
7. Saves files:
   - `backend/model/autoencoder.h5` (neural network)
   - `backend/model/autoencoder_scaler.pkl` (scaler)
   - `backend/model/autoencoder_threshold.json` (threshold)

**Output:**
```
Epoch 89/100 - loss: 0.0234 (early stopping triggered)
Threshold: 0.156 (95th percentile)
```

---

## 3. Docker Deployment Flow

### Step 1: Build Docker Image
```bash
cd docker/
docker-compose build --no-cache
```

**What Happens:**
1. Uses `python:3.10-slim` base image
2. Installs system dependencies (gcc, g++, etc.)
3. Installs Python packages from `requirements_api.txt`
4. Copies application code to `/app/`
5. Exposes port 8000
6. Sets uvicorn as entrypoint

**Image Size:** ~2.5 GB

### Step 2: Start Container
```bash
docker-compose up -d
```

**What Happens:**
1. Creates network: `fraud-net`
2. Starts container: `fraud-detection-api`
3. Mounts volume: `./backend/model:/app/backend/model`
4. Sets environment variables (DB credentials)
5. Starts uvicorn server on port 8000
6. Loads models on startup

**Container Status:**
```bash
docker ps
# STATUS: Up X minutes (healthy)
# PORTS: 0.0.0.0:8000->8000/tcp
```

### Step 3: Health Check
```bash
curl http://localhost:8000/api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T17:00:00",
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

## 4. Transaction Processing Flow

### Request Flow

```
Client (Postman/Frontend)
    ↓
POST /api/analyze-transaction
    ↓
FastAPI (api.py)
    ↓
┌─────────────────────────────────┐
│  1. Extract Request Data        │
│     - customer_id               │
│     - from_account_no           │
│     - to_account_no             │
│     - transaction_amount        │
│     - transfer_type             │
│     - datetime                  │
│     - bank_country              │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│  2. Fetch User Statistics       │
│     (db_service.py)             │
│                                 │
│  Database Queries:              │
│  - User average amount          │
│  - User std deviation           │
│  - User max amount              │
│  - Transaction frequency        │
│  - Weekly/Monthly stats         │
│  - Velocity metrics             │
│  - Beneficiary check            │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│  3. Feature Engineering         │
│     (feature_engineering.py)    │
│                                 │
│  Calculated Features:           │
│  - deviation_from_avg           │
│  - amount_to_max_ratio          │
│  - velocity_score               │
│  - time_based_features          │
│  - beneficiary_risk             │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│  4. Hybrid Decision             │
│     (hybrid_decision.py)        │
│                                 │
│  Three-Layer Check:             │
│  ┌───────────────────────────┐  │
│  │ A. Rule Engine            │  │
│  │    - Velocity limits      │  │
│  │    - Monthly spending     │  │
│  │    - Beneficiary check    │  │
│  │    Result: Pass/Fail      │  │
│  └───────────────────────────┘  │
│           ↓                     │
│  ┌───────────────────────────┐  │
│  │ B. Isolation Forest       │  │
│  │    - Load model           │  │
│  │    - Scale features       │  │
│  │    - Predict anomaly      │  │
│  │    Result: -1 or 1        │  │
│  └───────────────────────────┘  │
│           ↓                     │
│  ┌───────────────────────────┐  │
│  │ C. Autoencoder            │  │
│  │    - Load model           │  │
│  │    - Scale features       │  │
│  │    - Reconstruct input    │  │
│  │    - Calculate error      │  │
│  │    - Compare threshold    │  │
│  │    Result: Normal/Anomaly │  │
│  └───────────────────────────┘  │
│                                 │
│  Final Decision Logic:          │
│  - If Rule Engine fails → DENY  │
│  - If IF + AE both flag → DENY  │
│  - Otherwise → APPROVE          │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│  5. Generate Response           │
│                                 │
│  Response Fields:               │
│  - decision                     │
│  - risk_score                   │
│  - confidence_level             │
│  - reasons (list)               │
│  - individual_scores            │
│  - transaction_id               │
│  - processing_time_ms           │
└─────────────────────────────────┘
    ↓
Return JSON Response to Client
```

---

## 5. Detailed Component Flow

### A. Rule Engine Check
```python
# rule_engine.py

Input:
- amount: 500.3
- user_avg: 9124.09
- user_std: 19093.33
- transfer_type: "I"
- txn_count_10min: 1
- txn_count_1hour: 2
- monthly_spending: 410584.08
- is_new_beneficiary: 0

Process:
1. Calculate threshold = user_avg + (3.5 * user_std) = 76,000 AED
2. Check velocity: 1 < 5 (10min) ✓
3. Check velocity: 2 < 15 (1hour) ✓
4. Check spending: 410584 + 500 < 76000 ✗ FAIL
5. Check beneficiary: 0 (existing) ✓

Output:
- violated: True
- reasons: ["Monthly spending exceeds limit"]
- threshold: 76000.0
```

### B. Isolation Forest Check
```python
# isolation_forest.py

Input Features (45 features):
- transaction_amount: 500.3
- user_avg_amount: 9124.09
- deviation_from_avg: -8623.79
- velocity_score: 0.047
- ... (41 more features)

Process:
1. Load model: isolation_forest.pkl
2. Load scaler: isolation_forest_scaler.pkl
3. Scale features: X_scaled = scaler.transform(X)
4. Predict: model.predict(X_scaled)
5. Get anomaly score: model.score_samples(X_scaled)

Output:
- prediction: 1 (normal)
- anomaly_score: -0.053 (lower = more normal)
- is_anomaly: False
```

### C. Autoencoder Check
```python
# autoencoder.py

Input Features (45 features):
- Same as Isolation Forest

Process:
1. Load model: autoencoder.h5
2. Load scaler: autoencoder_scaler.pkl
3. Load threshold: autoencoder_threshold.json (0.156)
4. Scale features: X_scaled = scaler.transform(X)
5. Reconstruct: X_reconstructed = model.predict(X_scaled)
6. Calculate error: MSE(X_scaled, X_reconstructed)

Output:
- reconstruction_error: 0.090
- threshold: 0.156
- is_anomaly: False (0.090 < 0.156)
```

---

## 6. Example Transaction Flow

### Request
```json
POST http://localhost:8000/api/analyze-transaction

{
  "customer_id": "1000016",
  "from_account_no": "011000016019",
  "to_account_no": "AE040570000011049381018",
  "transaction_amount": 500.3,
  "transfer_type": "I",
  "datetime": "2025-07-05T16:17:00",
  "bank_country": "UAE"
}
```

### Processing Timeline
```
0ms    - Request received
10ms   - Database queries start
500ms  - User stats fetched
510ms  - Feature engineering complete
520ms  - Rule engine check (FAIL - monthly limit)
530ms  - Isolation Forest check (PASS - normal)
540ms  - Autoencoder check (PASS - normal)
550ms  - Decision: REQUIRES_USER_APPROVAL
560ms  - Response generated
```

### Response
```json
{
  "decision": "REQUIRES_USER_APPROVAL",
  "risk_score": -0.053,
  "confidence_level": 0.85,
  "reasons": [
    "Monthly spending AED 410,584.38 exceeds limit AED 76,000.00"
  ],
  "individual_scores": {
    "rule_engine": {
      "violated": true,
      "threshold": 76000.0
    },
    "isolation_forest": {
      "anomaly_score": -0.053,
      "is_anomaly": false
    },
    "autoencoder": {
      "reconstruction_error": 0.090,
      "is_anomaly": false
    }
  },
  "transaction_id": "txn_48cb17da",
  "processing_time_ms": 560
}
```

---

## 7. Database Integration

### Connection Flow
```
Container Startup
    ↓
Load Environment Variables
    ↓
DatabaseService.__init__()
    ↓
Connect to SQL Server
    ↓
Test Connection (SELECT 1)
    ↓
Connection Pool Ready
```

### Key Queries

**1. User Statistics**
```sql
SELECT 
    AVG(AmountInAed) as user_avg_amount,
    STDEV(AmountInAed) as user_std_amount,
    MAX(AmountInAed) as user_max_amount,
    COUNT(*) as user_txn_frequency
FROM TransactionHistoryLogs
WHERE CustomerId = ? AND FromAccountNo = ?
```

**2. Beneficiary Check**
```sql
SELECT COUNT(*) as count
FROM TransactionHistoryLogs
WHERE CustomerId = ? AND ReceipentAccount = ?
```

**3. Velocity Metrics**
```sql
SELECT 
    COUNT(CASE WHEN CreateDate >= DATEADD(MINUTE, -10, GETDATE()) THEN 1 END) as txn_count_10min,
    COUNT(CASE WHEN CreateDate >= DATEADD(HOUR, -1, GETDATE()) THEN 1 END) as txn_count_1hour
FROM TransactionHistoryLogs
WHERE CustomerId = ? AND FromAccountNo = ?
```

---

## 8. Monitoring & Logs

### Container Logs
```bash
# View real-time logs
docker logs fraud-detection-api -f

# View last 50 lines
docker logs fraud-detection-api --tail 50
```

### Log Levels
- **INFO**: Normal operations (requests, connections)
- **WARNING**: Model version mismatches, deprecations
- **ERROR**: Database failures, model load errors

### Key Log Messages
```
INFO: Connected using pymssql
INFO: Uvicorn running on http://0.0.0.0:8000
INFO: 172.18.0.1:43018 - "POST /api/analyze-transaction HTTP/1.1" 200 OK
ERROR: Connection failed with pymssql: <error details>
```

---

## 9. Troubleshooting

### Issue 1: Models Not Loading
**Symptom:** `Error loading model: No such file or directory`

**Solution:**
```bash
# Check if models exist
docker exec fraud-detection-api ls -la /app/backend/model/

# If missing, restart container (volume mount will sync)
docker-compose restart
```

### Issue 2: Database Connection Failed
**Symptom:** `Connection failed with pymssql`

**Solution:**
```bash
# Check environment variables
docker exec fraud-detection-api env | findstr DB_

# Test connection
docker exec -it fraud-detection-api bash
python -c "from backend.db_service import get_db_service; db = get_db_service(); print(db.connect())"
```

### Issue 3: Version Mismatch Warning
**Symptom:** `InconsistentVersionWarning: Trying to unpickle estimator`

**Solution:**
```bash
# Retrain models with matching scikit-learn version
pip install scikit-learn==1.7.2
python -m backend.train_isolation_forest
docker-compose restart
```

---

## 10. Performance Metrics

### Model Performance
- **Isolation Forest:** 5.03% anomaly detection rate
- **Autoencoder:** 95th percentile threshold (0.156)
- **Processing Time:** 500-1500ms per transaction

### Resource Usage
- **CPU:** 2-6 cores (configurable)
- **Memory:** 2-8 GB (configurable)
- **Disk:** ~3 GB (image + models)

### API Throughput
- **Single Request:** ~1 second
- **Concurrent Requests:** Depends on DB connection pool
- **Recommended:** Load balancer for production

---

## 11. Security Considerations

### Environment Variables
- Database credentials in `docker-compose.yml`
- Never commit `.env` file to Git
- Use secrets management in production

### Network Security
- Container isolated in `fraud-net` network
- Only port 8000 exposed
- Database connection encrypted (TrustServerCertificate)

### Model Security
- Models mounted as read-only in production
- Version control for model files
- Regular retraining with fresh data

---

## 12. Deployment Checklist

### Pre-Deployment
- [ ] Train models with latest data
- [ ] Test API locally
- [ ] Verify database connection
- [ ] Check environment variables
- [ ] Review Docker logs

### Deployment
- [ ] Build Docker image
- [ ] Start container
- [ ] Verify health endpoint
- [ ] Test sample transactions
- [ ] Monitor logs for errors

### Post-Deployment
- [ ] Set up monitoring
- [ ] Configure alerts
- [ ] Document API endpoints
- [ ] Train support team
- [ ] Schedule model retraining

---

## 13. Future Enhancements

### Planned Features
1. Real-time model updates
2. A/B testing for models
3. Enhanced logging (ELK stack)
4. Prometheus metrics
5. Kubernetes deployment
6. CI/CD pipeline
7. Automated model retraining
8. Multi-region deployment

---

## Conclusion

This fraud detection API uses a hybrid approach combining rule-based logic with machine learning models (Isolation Forest + Autoencoder) to detect fraudulent transactions. The system is containerized using Docker for easy deployment and scalability.

**Key Strengths:**
- Multi-layer fraud detection
- Real-time processing
- Database integration
- Containerized deployment
- Comprehensive logging


