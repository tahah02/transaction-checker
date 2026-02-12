# Banking Fraud Detection API - Complete Project Architecture

## Table of Contents
1. Project Overview
2. System Architecture
3. Core Components
4. Database Schema
5. API Endpoints
6. Data Flows
7. Security Implementation
8. Deployment

---

## 1. Project Overview

Banking Fraud Detection API ek real-time fraud detection system hai jo triple-layer security use karta hai:
- Rule Engine (Business Rules)
- Isolation Forest (ML Model)
- Autoencoder (Deep Learning)

**Key Features:**
- Real-time transaction analysis
- Idempotence key support (duplicate prevention)
- Admin-only approval/rejection
- Complete audit logging
- Connection pooling for performance

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Application                       │
│                    (Postman / Frontend)                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Server                            │
│                   (api/api.py)                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Endpoints:                                           │   │
│  │ - POST /api/analyze-transaction                      │   │
│  │ - POST /api/transaction/approve                      │   │
│  │ - POST /api/transaction/reject                       │   │
│  │ - GET /api/transactions/pending                      │   │
│  │ - GET /api/health                                    │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ↓                ↓                ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Helpers    │  │   Services   │  │   Models     │
│ (api/helpers)│  │(api/services)│  │(api/models)  │
└──────────────┘  └──────────────┘  └──────────────┘
        │                │                │
        └────────────────┼────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                  Backend Processing                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ - Rule Engine (backend/rule_engine.py)              │   │
│  │ - Isolation Forest (backend/isolation_forest.py)    │   │
│  │ - Autoencoder (backend/autoencoder.py)              │   │
│  │ - Hybrid Decision (backend/hybrid_decision.py)      │   │
│  │ - Feature Engineering (backend/feature_engineering) │   │
│  │ - Input Validator (backend/input_validator.py)      │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              Database Service Layer                          │
│            (backend/db_service.py)                           │
│  - Connection Pooling (pymssql)                              │
│  - Query Execution                                           │
│  - Transaction Management                                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                  MSSQL Database                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Tables:                                              │   │
│  │ - TransactionHistoryLogs (source data)              │   │
│  │ - APITransactionLogs (fraud detection results)      │   │
│  │ - TransactionLogs (audit trail + idempotence)       │   │
│  │ - FeaturesConfig (feature flags)                    │   │
│  │ - ModelVersionConfig (model tracking)               │   │
│  │ - ThresholdConfig (threshold management)            │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Core Components

### 3.1 api/api.py - FastAPI Application

**Purpose:** Main API server aur endpoints

**Key Functions:**
- `health_check()` - Server health status
- `analyze_transaction()` - Fraud detection
- `approve_transaction()` - Admin approval
- `reject_transaction()` - Admin rejection
- `list_pending_transactions()` - Pending list
- `get_all_features()` - Feature list
- `enable_feature()` - Enable feature flag
- `disable_feature()` - Disable feature flag

**Key Logic:**
```
analyze_transaction():
  1. Verify basic auth
  2. Generate/use idempotence_key
  3. Check if duplicate (cached response)
  4. Validate request
  5. Get user statistics from DB
  6. Check new beneficiary
  7. Get velocity metrics
  8. Run fraud detection (3 models)
  9. Make decision
  10. Log to TransactionLogs
  11. Return response with idempotence_key
```

### 3.2 api/helpers.py - Helper Functions

**Purpose:** Utility functions for API operations

**Key Functions:**
- `verify_basic_auth()` - API authentication
- `verify_admin_key()` - Admin verification
- `validate_transfer_request()` - Request validation
- `save_transaction_to_file()` - Save to DB + TransactionLogs
- `update_transaction_status()` - Update approval/rejection
- `generate_idempotence_key()` - UUID generation
- `check_idempotence()` - Duplicate detection

### 3.3 api/models.py - Pydantic Models

**Purpose:** Request/Response data validation

**Models:**
- `TransactionRequest` - Fraud detection request
- `TransactionResponse` - Fraud detection response
- `ApprovalRequest` - Approval request
- `RejectionRequest` - Rejection request
- `ActionResponse` - Action response

### 3.4 backend/db_service.py - Database Service

**Purpose:** Database operations aur connection management

**Key Features:**
- Connection pooling (pymssql)
- Query execution
- Transaction management
- User statistics retrieval
- Beneficiary checking
- Velocity metrics

**Key Methods:**
- `connect()` - Establish connection
- `disconnect()` - Close connection
- `execute_query()` - SELECT queries
- `execute_non_query()` - INSERT/UPDATE/DELETE
- `get_all_user_stats()` - User statistics
- `check_new_beneficiary()` - Beneficiary check
- `get_velocity_metrics()` - Velocity data
- `insert_transaction_log()` - Log insertion
- `get_transaction_log_by_idempotence_key()` - Log retrieval

### 3.5 backend/rule_engine.py - Business Rules

**Purpose:** Rule-based fraud detection

**Rules:**
- Velocity limits (10min, 1hour)
- Monthly spending threshold
- New beneficiary flag
- Amount threshold calculation

**Key Functions:**
- `calculate_threshold()` - Dynamic threshold
- `check_rule_violation()` - Rule checking

### 3.6 backend/isolation_forest.py - ML Model

**Purpose:** Anomaly detection using Isolation Forest

**Features:**
- Unsupervised learning
- Anomaly scoring
- Threshold-based detection

### 3.7 backend/autoencoder.py - Deep Learning

**Purpose:** Reconstruction error-based detection

**Features:**
- Neural network model
- Reconstruction error calculation
- Threshold-based flagging

### 3.8 backend/hybrid_decision.py - Decision Engine

**Purpose:** Combine 3 models aur final decision

**Logic:**
```
make_decision():
  1. Rule Engine check
  2. Isolation Forest score
  3. Autoencoder error
  4. Combine scores
  5. Calculate confidence
  6. Model agreement
  7. Final decision
```

### 3.9 backend/feature_engineering.py - Feature Processing

**Purpose:** Feature extraction aur transformation

**Features:**
- Data preprocessing
- Feature scaling
- Feature selection

### 3.10 backend/input_validator.py - Input Validation

**Purpose:** Request data validation

**Validations:**
- Required fields check
- Data type validation
- Range validation

---

## 4. Database Schema

### TransactionHistoryLogs
Source data table - historical transactions

### APITransactionLogs
Fraud detection results - decision, risk score, model outputs

### TransactionLogs
Audit trail + idempotence cache
- IdempotenceKey (UNIQUE)
- RequestPayload (JSON)
- ResponsePayload (JSON)
- IsSuccessful (BIT)
- Decision (NVARCHAR)

### FeaturesConfig
Feature flags management

### ModelVersionConfig
Model version tracking

### ThresholdConfig
Threshold management

---

## 5. API Endpoints

### 5.1 POST /api/analyze-transaction

**Purpose:** Fraud detection

**Request:**
```json
{
  "customer_id": "1000016",
  "from_account_no": "011000016033",
  "from_account_currency": "AED",
  "to_account_no": "011000016019",
  "transaction_amount": 750,
  "transfer_currency": "AED",
  "transfer_type": "O",
  "charges_type": "SHA",
  "swift": "DEUTDEFJ",
  "check_constraint": true,
  "bank_country": "UAE",
  "idempotence_key": null
}
```

**Response:**
```json
{
  "advice": "APPROVED",
  "risk_score": 0.25,
  "risk_level": "SAFE",
  "confidence_level": 0.95,
  "model_agreement": 0.87,
  "reasons": [],
  "individual_scores": {...},
  "transaction_id": "txn_abc12345",
  "processing_time_ms": 245,
  "idempotence_key": "550e8400-e29b-41d4-a716-446655440000",
  "is_cached": false
}
```

### 5.2 POST /api/transaction/approve

**Purpose:** Admin approval

**Request:**
```json
{
  "transaction_id": "txn_abc12345",
  "customer_id": "1000016",
  "admin_key": "FDS12345",
  "comments": "Approved"
}
```

### 5.3 POST /api/transaction/reject

**Purpose:** Admin rejection

**Request:**
```json
{
  "transaction_id": "txn_abc12345",
  "customer_id": "1000016",
  "admin_key": "FDS12345",
  "reason": "Suspicious activity"
}
```

### 5.4 GET /api/transactions/pending

**Purpose:** List pending transactions

### 5.5 GET /api/health

**Purpose:** Health check

---

## 6. Data Flows

### Flow 1: Transaction Analysis (New Request)

```
Client Request
    ↓
API Endpoint (analyze_transaction)
    ↓
Verify Auth (Basic Auth)
    ↓
Generate IdempotenceKey (UUID)
    ↓
Check Idempotence (DB Query)
    ↓
Key Not Found → Continue
    ↓
Validate Request
    ↓
Get User Statistics (DB)
    ↓
Check New Beneficiary (DB)
    ↓
Get Velocity Metrics (DB)
    ↓
Run Fraud Detection:
  ├─ Rule Engine
  ├─ Isolation Forest
  └─ Autoencoder
    ↓
Combine Results
    ↓
Make Decision
    ↓
Save to APITransactionLogs (DB)
    ↓
Insert to TransactionLogs (DB)
    ↓
Return Response with IdempotenceKey
    ↓
Client Receives Response
```

### Flow 2: Transaction Analysis (Duplicate Request)

```
Client Request (Same IdempotenceKey)
    ↓
API Endpoint (analyze_transaction)
    ↓
Verify Auth
    ↓
Use Provided IdempotenceKey
    ↓
Check Idempotence (DB Query)
    ↓
Key Found + IsSuccessful = 1
    ↓
Retrieve Cached Response
    ↓
Return Cached Response (is_cached=true)
    ↓
Client Receives Response (No Processing)
```

### Flow 3: Transaction Approval

```
Client Request (Approval)
    ↓
API Endpoint (approve_transaction)
    ↓
Verify Basic Auth
    ↓
Verify Admin Key
    ↓
Update APITransactionLogs (UserAction=APPROVED)
    ↓
Insert to TransactionLogs (Audit Log)
    ↓
Return Success Response
    ↓
Client Receives Response
```

### Flow 4: Complete End-to-End Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. CLIENT INITIATES REQUEST                                 │
│    - Sends transaction data                                  │
│    - Optional: idempotence_key                               │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. API AUTHENTICATION                                        │
│    - Verify Basic Auth (API_USERNAME, API_PASSWORD)         │
│    - Check Authorization header                              │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. IDEMPOTENCE CHECK                                         │
│    - Generate UUID if not provided                           │
│    - Query TransactionLogs table                             │
│    - If found + successful → Return cached response          │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. REQUEST VALIDATION                                        │
│    - Validate transfer type                                  │
│    - Validate currencies                                     │
│    - Validate required fields                                │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. DATA RETRIEVAL                                            │
│    - Get user statistics (avg, std, max amount)              │
│    - Check new beneficiary                                   │
│    - Get velocity metrics (10min, 1hour)                     │
│    - Get monthly spending                                    │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. FRAUD DETECTION (3 Models)                                │
│                                                               │
│    Rule Engine:                                              │
│    ├─ Check velocity limits                                  │
│    ├─ Check monthly threshold                                │
│    └─ Check new beneficiary                                  │
│                                                               │
│    Isolation Forest:                                         │
│    ├─ Calculate anomaly score                                │
│    └─ Compare with threshold                                 │
│                                                               │
│    Autoencoder:                                              │
│    ├─ Calculate reconstruction error                         │
│    └─ Compare with threshold                                 │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. DECISION MAKING                                           │
│    - Combine 3 model outputs                                 │
│    - Calculate confidence level                              │
│    - Calculate model agreement                               │
│    - Determine final decision:                               │
│      * APPROVED (Low risk)                                   │
│      * REQUIRES_USER_APPROVAL (Medium risk)                  │
│      * BLOCK_AND_VERIFY (High risk)                          │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ 8. DATABASE LOGGING                                          │
│    - Insert to APITransactionLogs (fraud detection results)  │
│    - Insert to TransactionLogs (audit trail + cache)         │
│    - Store request/response payloads (JSON)                  │
│    - Store idempotence_key (UNIQUE)                          │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ 9. RESPONSE GENERATION                                       │
│    - Include decision                                        │
│    - Include risk score                                      │
│    - Include individual model scores                         │
│    - Include idempotence_key                                 │
│    - Include is_cached flag                                  │
│    - Include processing_time_ms                              │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ 10. CLIENT RECEIVES RESPONSE                                 │
│     - Stores idempotence_key for retry                       │
│     - Processes decision                                     │
│     - Takes action (approve/reject/notify)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Security Implementation

### Authentication
- Basic Auth (API_USERNAME, API_PASSWORD)
- Base64 encoding
- Environment variables

### Authorization
- Admin Key verification (ADMIN_KEY)
- Role-based access control

### Data Protection
- Idempotence key (duplicate prevention)
- Audit logging (TransactionLogs)
- Request/response payload storage

### Database Security
- Connection pooling
- Parameterized queries
- Transaction management

---

## 8. Deployment

### Docker Setup
- Python 3.10 slim image
- FreeTDS for MSSQL connection
- FastAPI + Uvicorn
- Volume mounting for models

### Environment Variables
```
DB_SERVER=10.112.32.4
DB_PORT=1433
DB_DATABASE=retailchannelLogs
DB_USERNAME=dbuser
DB_PASSWORD=***
API_USERNAME=FDS
API_PASSWORD=12345
ADMIN_KEY=FDS12345
```

### Commands
```
docker-compose -f Docker/docker-compose.yml build
docker-compose -f Docker/docker-compose.yml up -d
docker-compose -f Docker/docker-compose.yml logs -f
```

---

**Document Version:** 1.0
**Last Updated:** February 12, 2026
**Status:** Complete
