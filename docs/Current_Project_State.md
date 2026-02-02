# Banking Fraud Detection System - Current Project State

**Last Updated:** January 29, 2026  
**Status:** Production Ready - Deployed on Docker

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Feature Dataset Documentation](#feature-dataset-documentation)
3. [Model Training & Architecture](#model-training--architecture)
4. [Security Improvements](#security-improvements)
5. [API Documentation](#api-documentation)
6. [Deployment Architecture](#deployment-architecture)
7. [Current Issues & Roadmap](#current-issues--roadmap)

---

## Project Overview

A real-time banking fraud detection system that combines rule-based engines with machine learning models (Isolation Forest & Autoencoder) to identify anomalous transactions. The system is deployed as a containerized FastAPI application with a Streamlit frontend for manual transaction testing.

**Tech Stack:**
- **Backend:** FastAPI, Python 3.10
- **ML Models:** Isolation Forest, Autoencoder (TensorFlow/Keras)
- **Database:** Microsoft SQL Server (pymssql driver)
- **Deployment:** Docker, Docker Compose
- **Frontend:** Streamlit (port 8502)
- **API:** FastAPI (port 8000)

---

## Feature Dataset Documentation

### Dataset: `feature_datasetv2.csv`

**Feature Calculation Logic:**  
Every feature is calculated using `Customer_ID + Account_No` combination to ensure fraud detection works independently for each customer's individual accounts.

### Feature Categories

#### 1. Core Features (4 features)

| Feature | Description | Values/Logic |
|---------|-------------|--------------|
| **Txn_amount** | Transaction amount in AED | Continuous value |
| **Flag_amount** | International transfer flag | 1 if transfer_type='S', else 0 |
| **Transfer_type_Risk_score** | Hardcoded risk scores | S=0.9, Q=0.5, L=0.2, I=0.1, O=0.0, M=0.3, F=0.15 |
| **Transfer_type_encoded** | Numeric encoding | S=4, Q=3, L=2, I=1, O=0, M=5, F=6 |

**Transfer Types:**
- **S** - Overseas (Highest risk: 0.9)
- **Q** - Quick Remittance (Medium risk: 0.5)
- **L** - Within UAE (Low risk: 0.2)
- **I** - Within Ajman (Very low risk: 0.1)
- **O** - Own Account (No risk: 0.0)
- **M** - MobilePay (Low-Medium risk: 0.3)
- **F** - Family Transfer (Very low risk: 0.15)

#### 2. Temporal Features (7 features)

| Feature | Description | Calculation |
|---------|-------------|-------------|
| **Hour** | Transaction hour (0-23) | Extracted from timestamp |
| **Day_of_the_week** | Day of week (0-6) | Monday=0, Sunday=6 |
| **Is_weekend** | Weekend flag | 1 if day in [5,6], else 0 |
| **Is_night** | Night transaction flag | 1 if hour between 22-6, else 0 |
| **Time_since_last_txn** | Seconds since last transaction | current_time - last_txn_time |
| **Recent_burst** | Burst activity indicator | 1 if time_since_last < 300s, else 0 |
| **Txn_velocity** | Transactions per hour rate | 3600 / time_since_last_txn |

#### 3. User Behavioral Features (7 features)

| Feature | Description | Formula |
|---------|-------------|---------|
| **User_avg_amount** | Historical average | mean(all user transactions) |
| **User_std_amount** | Standard deviation | sqrt(variance of amounts) |
| **User_max_amount** | Maximum transaction | max(user transactions) |
| **User_txn_frequency** | Total transaction count | count(user transactions) |
| **Deviation_from_avg** | Current deviation | abs(amount - user_avg) |
| **Amount_to_max_ratio** | Ratio to max | amount / user_max |
| **Intl_ratio** | International ratio | count(S_type) / total_txns |

**Standard Deviation Calculation:**
1. Calculate: (txn_amount - historical_avg)
2. Square the result
3. Sum all squared values
4. Variance = sum / total_transactions
5. Std_dev = sqrt(variance)

#### 4. Account & Relationship Features (6 features)

| Feature | Description | Logic |
|---------|-------------|-------|
| **num_of_accounts** | Total accounts per customer | count(distinct accounts) |
| **user_multiple_acc_flag** | Multiple account indicator | 1 if num_accounts > 1, else 0 |
| **cross_account_transfer_ratio** | Cross-account activity | cross_acc_txns / total_txns |
| **geo_anomaly_flag** | Geographic anomaly | 1 if unique_countries > 2, else 0 |
| **is_new_beneficiary** | New recipient flag | 1 if beneficiary not in history, else 0 |
| **ben_txn_count_30days** | Beneficiary transaction count | count(txns to this beneficiary in 30d) |

#### 5. Velocity & Frequency Features (7 features)

| Feature | Description | Window |
|---------|-------------|--------|
| **txn_count_30s** | Transaction count | Last 30 seconds |
| **txn_count_10min** | Transaction count | Last 10 minutes |
| **txn_count_1hr** | Transaction count | Last 1 hour |
| **hourly_total** | Sum of amounts | Current hour |
| **hourly_count** | Transaction count | Current hour |
| **daily_total** | Sum of amounts | Current day |
| **daily_count** | Transaction count | Current day |

#### 6. Advanced Analytical Features (11 features)

| Feature | Description | Formula |
|---------|-------------|---------|
| **weekly_total** | Weekly spending | sum(txns in week) |
| **weekly_txn_count** | Weekly transaction count | count(txns in week) |
| **weekly_avg** | Weekly average | mean(weekly txns) |
| **weekly_deviation** | Deviation from weekly avg | abs(amount - weekly_avg) |
| **amount_vs_weekly_avg** | Ratio to weekly avg | amount / weekly_avg |
| **current_month_spending** | Monthly spending | sum(txns this month) |
| **monthly_txn_count** | Monthly transaction count | count(txns this month) |
| **monthly_avg_amount** | Monthly average | mean(monthly txns) |
| **monthly_deviation** | Deviation from monthly avg | abs(amount - monthly_avg) |
| **amount_vs_monthly_avg** | Ratio to monthly avg | amount / monthly_avg |
| **rolling_std** | Rolling standard deviation | std(last 5 txns) |

**Rolling Standard Deviation Formula:**
```
rolling_std = sqrt(sum((each_amount - avg)²) / 4)
```
High rolling_std indicates volatile/anomalous behavior. First transaction always returns 0.

---

## Model Training & Architecture

### 1. Isolation Forest

**Purpose:** Detects anomalies by isolating outliers using ensemble of decision trees.

**Architecture:**
- **n_estimators:** 100 trees
- **contamination:** 0.1 (10% expected fraud rate)
- **random_state:** 42 (reproducible results)
- **max_samples:** 'auto' (256 samples per tree)
- **max_features:** 1.0 (uses all 42 features)

**How It Works:**
1. Creates 100 isolation trees with random splits
2. Each tree uses random feature subsets
3. Anomalies require fewer splits to isolate
4. Calculates average path length across all trees
5. Shorter paths = higher anomaly score

**Anomaly Score Formula:**
```
Anomaly_Score = 2^(-Average_Path_Length / c(n))
where c(n) = 2 * (ln(n-1) + 0.5772) - 2(n-1)/n
```

**Decision Logic:**
- Score > 0.5 → Anomaly
- Score ≤ 0.5 → Normal

**Example - Normal Transaction:**
```
Customer_ID: 1000016
Amount: 500.3 AED
Transfer_type: S
Features: amount=500.3, deviation=8623.79, user_avg=9124.09
Average path length: 8.7 splits
Anomaly score: 2^(-8.7/10.41) = 0.69 → NORMAL
```

**Example - Anomalous Transaction:**
```
Customer_ID: 1000016
Amount: 373.56 AED
Deviation: 8748.53
Txn_count_1hr: 5
Txn_velocity: 10.14
Average path length: 3.4 splits (easily isolated)
Anomaly score: 2^(-3.4/10.41) = 0.797 → ANOMALY
```

### 2. Autoencoder Neural Network

**Purpose:** Learns normal transaction patterns and flags high reconstruction errors as anomalies.

**Architecture:**
```
Input Layer (42 features)
    ↓
Encoder Layer 1 (64 neurons, ReLU)
    ↓
Encoder Layer 2 (32 neurons, ReLU)
    ↓
Bottleneck (14 neurons) ← Compressed representation
    ↓
Decoder Layer 1 (32 neurons, ReLU)
    ↓
Decoder Layer 2 (64 neurons, ReLU)
    ↓
Output Layer (42 features)
```

**Training Configuration:**
- **Epochs:** 100 (with early stopping)
- **Batch size:** 64 transactions
- **Validation split:** 0.1 (90% train, 10% validation)
- **Optimizer:** Adam (adaptive learning rate)
- **Loss function:** Mean Squared Error (MSE)
- **Early stopping:** Patience of 5 epochs

**Training Process:**
1. **Encoding:** Compresses 42 features → 64 → 32 → 14 neurons
2. **Bottleneck:** Forces model to learn essential patterns in 14 dimensions
3. **Decoding:** Reconstructs 14 → 32 → 64 → 42 features
4. **Validation:** Stops training when validation loss stops improving

**Actual Training Results:**
- Model trained for 54 epochs
- Early stopping triggered at epoch 59 (patience=5)
- Prevented overfitting by stopping when validation loss plateaued

**Decision Logic:**
```
MSE = Average of (predicted - actual)²

If MSE > 0.070:
    return "ANOMALY - Poor reconstruction"
Else:
    return "NORMAL - Good reconstruction"
```

**Why MSE?**
- Perfect for measuring reconstruction quality
- Works well with continuous transaction features
- Penalizes large errors more than small ones

### 3. Rule Engine

**Hardcoded Business Rules:**

**Transfer Type Limits:**
```python
TRANSFER_MULTIPLIERS = {
    'S': 2.0,  # Overseas
    'Q': 2.5,  # Quick Remittance
    'L': 3.0,  # Within UAE
    'I': 3.5,  # Within Ajman
    'O': 4.0,  # Own Account
    'M': 3.2,  # MobilePay
    'F': 3.8   # Family Transfer
}

TRANSFER_MIN_FLOORS = {
    'S': 5000,  # Minimum AED 5,000
    'Q': 3000,  # Minimum AED 3,000
    'L': 2000,  # Minimum AED 2,000
    'I': 1500,  # Minimum AED 1,500
    'O': 1000,  # Minimum AED 1,000
    'M': 1800,  # Minimum AED 1,800
    'F': 1200   # Minimum AED 1,200
}
```

**Threshold Calculation:**
```
threshold = max(user_avg + multiplier × user_std, floor)
```

**Velocity Limits:**
- **10 minutes:** Maximum 5 transactions
- **1 hour:** Maximum 15 transactions

**Violation Checks:**
1. Velocity check (10min & 1hr)
2. Monthly spending limit check
3. New beneficiary flag check

### 4. Hybrid Decision Logic

**Decision Flow:**
```
1. Rule Engine Check
   ↓
2. Isolation Forest Check (if rules pass)
   ↓
3. Autoencoder Check (if IF passes)
   ↓
4. Final Decision: ANY violation = FRAUD
```

**Conservative Approach:**
- If ANY layer flags fraud → Transaction requires approval
- Matches real-world banking: safety over convenience
- No single layer can override others

---

## Security Improvements

### Critical Fixes Applied

#### 1. Credentials Moved to Environment Variables
**Before:** Database credentials hardcoded in source files  
**After:** All secrets stored in `.env` file and loaded at runtime  
**Impact:** No secrets exposed in codebase or version control

#### 2. Parameterized SQL Queries
**Before:** User input directly concatenated into SQL queries  
**After:** All queries use parameterized statements  
**Impact:** SQL injection attacks completely blocked

#### 3. Strict Input Validation
**Before:** Invalid data could reach deep into the system  
**After:** All requests validated at API entry point  
**Checks:**
- Amount > 0
- Valid transfer types (S, I, L, Q, O, M, F)
- Valid datetime format
- Proper account number format
- Customer ID exists

**Impact:** Malformed/malicious requests rejected immediately

#### 4. Redis-Backed Velocity Tracking
**Before:** Velocity metrics reset on application restart  
**After:** Transaction history persisted in Redis  
**Impact:** Prevents restart-based fraud bypass

#### 5. Atomic File Operations
**Before:** Race conditions possible during concurrent file writes  
**After:** File operations use locks and atomic writes  
**Impact:** Eliminates data corruption

#### 6. Memory Cleanup Logic
**Before:** Memory leaks during long-running operations  
**After:** Automatic cleanup of unused data  
**Impact:** Consistent performance over time

#### 7. Fraud Voting Logic Fixed
**Before:** Detection layers could override each other  
**After:** Conservative "any violation = fraud" approach  
**Impact:** No risky transactions slip through

---

## API Documentation

### Base URL
- **Local:** `http://localhost:8000`
- **Network:** `http://192.168.18.21:8000` (your current IP)
- **Docker:** `http://0.0.0.0:8000`

### Endpoints

#### 1. Health Check
**GET** `/api/health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-29T15:25:02.234043",
  "models": {
    "isolation_forest": "loaded",
    "autoencoder": "loaded"
  },
  "database": {
    "status": "connected"
  }
}
```

#### 2. Analyze Transaction
**POST** `/api/analyze-transaction`

**Request Body:**
```json
{
  "customer_id": "1000166",
  "from_account_no": "11000166016",
  "to_account_no": "UA123456789",
  "transaction_amount": 500,
  "transfer_type": "O",
  "datetime": "2026-01-29T10:00:00",
  "bank_country": "UAE"
}
```

**Response - Normal Transaction:**
```json
{
  "decision": "APPROVED",
  "risk_score": -0.054920817561168955,
  "confidence_level": 0.85,
  "reasons": [],
  "individual_scores": {
    "rule_engine": {
      "violated": false,
      "threshold": 406324.53979323286
    },
    "isolation_forest": {
      "anomaly_score": -0.054920817561168955,
      "is_anomaly": false
    },
    "autoencoder": {
      "reconstruction_error": 0.045,
      "is_anomaly": false
    }
  },
  "transaction_id": "txn_a1b2c3d4",
  "processing_time_ms": 29
}
```

**Response - Anomalous Transaction (Limit Exceeded):**
```json
{
  "decision": "REQUIRES_USER_APPROVAL",
  "risk_score": -0.05814711163930125,
  "confidence_level": 0.85,
  "reasons": [
    "Monthly spending AED 10,000.00 exceeds limit AED 5,000.00"
  ],
  "individual_scores": {
    "rule_engine": {
      "violated": true,
      "threshold": 5000
    },
    "isolation_forest": {
      "anomaly_score": -0.05814711163930125,
      "is_anomaly": false
    },
    "autoencoder": {
      "reconstruction_error": 0.052,
      "is_anomaly": false
    }
  },
  "transaction_id": "txn_e5f6g7h8",
  "processing_time_ms": 14
}
```

**Response - Anomalous Transaction (Burst Activity):**
```json
{
  "decision": "REQUIRES_USER_APPROVAL",
  "risk_score": 0.008969754654172823,
  "confidence_level": 0.85,
  "reasons": [
    "Velocity limit exceeded: 6 transactions in last 10 minutes (max allowed 5)",
    "ML anomaly detected: abnormal behavior pattern (risk score 0.0090)"
  ],
  "individual_scores": {
    "rule_engine": {
      "violated": true,
      "threshold": 13000.0
    },
    "isolation_forest": {
      "anomaly_score": 0.008969754654172823,
      "is_anomaly": true
    },
    "autoencoder": {
      "reconstruction_error": 0.082,
      "is_anomaly": true
    }
  },
  "transaction_id": "txn_i9j0k1l2",
  "processing_time_ms": 28
}
```

**Response - New Beneficiary:**
```json
{
  "decision": "REQUIRES_USER_APPROVAL",
  "risk_score": -0.045,
  "confidence_level": 0.85,
  "reasons": [
    "New beneficiary detected - first time transaction to this recipient requires approval"
  ],
  "individual_scores": {
    "rule_engine": {
      "violated": true,
      "threshold": 15000.0
    },
    "isolation_forest": {
      "anomaly_score": -0.045,
      "is_anomaly": false
    },
    "autoencoder": {
      "reconstruction_error": 0.038,
      "is_anomaly": false
    }
  },
  "transaction_id": "txn_m3n4o5p6",
  "processing_time_ms": 22
}
```

#### 3. Approve Transaction
**POST** `/api/transaction/approve`

**Request Body:**
```json
{
  "transaction_id": "txn_a1b2c3d4",
  "customer_id": "1000166",
  "comments": "Verified with customer via phone"
}
```

**Response:**
```json
{
  "status": "approved",
  "transaction_id": "txn_a1b2c3d4",
  "timestamp": "2026-01-29T15:30:00",
  "message": "Transaction approved successfully"
}
```

#### 4. Reject Transaction
**POST** `/api/transaction/reject`

**Request Body:**
```json
{
  "transaction_id": "txn_e5f6g7h8",
  "customer_id": "1000212",
  "reason": "Suspicious activity pattern detected"
}
```

**Response:**
```json
{
  "status": "rejected",
  "transaction_id": "txn_e5f6g7h8",
  "timestamp": "2026-01-29T15:35:00",
  "message": "Transaction rejected successfully"
}
```

#### 5. Get Pending Transactions
**GET** `/api/transactions/pending`

**Response:**
```json
{
  "count": 3,
  "transactions": [
    {
      "transaction_id": "txn_a1b2c3d4",
      "customer_id": "1000166",
      "from_account": "11000166016",
      "to_account": "UA123456789",
      "amount": 5000.0,
      "transfer_type": "S",
      "decision": "REQUIRES_USER_APPROVAL",
      "risk_score": 0.75,
      "reasons": "Monthly spending exceeds limit",
      "timestamp": "2026-01-29T15:20:00"
    }
  ]
}
```

---

## Deployment Architecture

### Docker Configuration

**Container Details:**
- **Image:** Python 3.10-slim
- **Container Name:** fraud-detection-api
- **Ports:** 8000:8000 (API), 8502:8502 (Streamlit)
- **Network:** Bridge network (fraud-net)

**Resource Limits:**
- **CPU:** 2-6 cores (min-max)
- **Memory:** 2-8 GB (min-max)
- **Restart Policy:** unless-stopped

**Volumes Mounted:**
- `../backend/model:/app/backend/model` (Model files)
- `../data:/app/data` (Transaction data)

**Environment Variables:**
```env
DB_SERVER=10.112.32.4
DB_PORT=1433
DB_DATABASE=retailchannelLogs
DB_USERNAME=dbuser
DB_PASSWORD=Codebase202212?!
PYTHONUNBUFFERED=1
```

**Health Check:**
- **Interval:** 30 seconds
- **Timeout:** 10 seconds
- **Start Period:** 40 seconds
- **Retries:** 3
- **Command:** HTTP GET to `/api/health`

### Running the System

**Start Docker Container:**
```bash
cd Docker
docker-compose up -d
```

**Check Container Status:**
```bash
docker ps
```

**View Logs:**
```bash
docker logs fraud-detection-api
```

**Stop Container:**
```bash
docker-compose down
```

**Start Streamlit App (Local):**
```bash
streamlit run app.py --server.port 8502
```

### Network Access

**Local Access:**
- API: `http://localhost:8000`
- Streamlit: `http://localhost:8502`

**Network Access (Same WiFi):**
- API: `http://192.168.18.21:8000`
- Streamlit: `http://192.168.18.21:8502`

**Note:** Ensure Windows Firewall allows incoming connections on ports 8000 and 8502.

---

## Current Issues & Roadmap

### Known Issues

1. **Streamlit Label Warnings**
   - **Issue:** Empty label warnings in Streamlit UI
   - **Impact:** Cosmetic only, no functional impact
   - **Fix:** Add `label_visibility="collapsed"` to input widgets
   - **Priority:** Low

2. **Database Connection Dependency**
   - **Issue:** API requires database connection for beneficiary checks
   - **Impact:** Returns 503 error if database unavailable
   - **Workaround:** Fallback to assume existing beneficiary
   - **Priority:** Medium

3. **Redis Not Implemented**
   - **Issue:** Velocity tracking uses CSV files instead of Redis
   - **Impact:** Slower performance, restart vulnerability
   - **Fix:** Implement Redis caching layer
   - **Priority:** High

### Completed Features

✅ Docker deployment with health checks  
✅ Hybrid fraud detection (Rules + IF + AE)  
✅ New beneficiary detection  
✅ Transaction approval/rejection workflow  
✅ Pending transactions tracking  
✅ Security hardening (SQL injection, input validation)  
✅ Environment variable configuration  
✅ Network accessibility (0.0.0.0 binding)  

### Roadmap

**Short Term (1-2 weeks):**
- [ ] Fix Streamlit label warnings
- [ ] Implement Redis for velocity tracking
- [ ] Add API rate limiting
- [ ] Improve error messages
- [ ] Add transaction history endpoint

**Medium Term (1 month):**
- [ ] Add user authentication to API
- [ ] Implement webhook notifications
- [ ] Add dashboard for fraud analytics
- [ ] Model retraining pipeline
- [ ] Performance optimization

**Long Term (3+ months):**
- [ ] Multi-tenant support
- [ ] Real-time alerting system
- [ ] Advanced ML models (LSTM, Transformer)
- [ ] A/B testing framework
- [ ] Kubernetes deployment

---

## File Structure

```
project/
├── api/
│   ├── api.py              # Main API endpoints
│   ├── models.py           # Pydantic models
│   ├── services.py         # Business logic
│   └── helpers.py          # Utility functions
├── backend/
│   ├── autoencoder.py      # Autoencoder model
│   ├── db_service.py       # Database operations
│   ├── feature_engineering.py
│   ├── hybrid_decision.py  # Decision logic
│   ├── input_validator.py  # Input validation
│   ├── isolation_forest.py # IF model
│   ├── rule_engine.py      # Business rules
│   ├── utils.py            # Utilities
│   ├── velocity_service.py # Velocity tracking
│   └── model/              # Trained models
│       ├── autoencoder.h5
│       ├── autoencoder_scaler.pkl
│       ├── autoencoder_threshold.json
│       ├── isolation_forest.pkl
│       └── isolation_forest_scaler.pkl
├── data/
│   ├── api_transactions.csv
│   ├── feature_datasetv2.csv
│   └── transaction_history.csv
├── Docker/
│   ├── docker-compose.yml
│   └── Dockerfile
├── docs/
│   └── Current_Project_State.md (this file)
├── app.py                  # Streamlit frontend
├── api.py                  # API entry point
├── .env                    # Environment variables
├── requirements.txt        # Python dependencies
└── requirements_api.txt    # API-specific dependencies
```

---

## Contact & Support

**Project Status:** Production Ready  
**Last Deployment:** January 29, 2026  
**Docker Status:** Running (fraud-detection-api)  
**API Status:** Healthy  
**Database Status:** Connected  

**Network Configuration:**
- Local IP: 192.168.18.21
- API Port: 8000
- Streamlit Port: 8502
- Database: 10.112.32.4:1433

---

**Document Version:** 1.0  
**Generated:** January 29, 2026
