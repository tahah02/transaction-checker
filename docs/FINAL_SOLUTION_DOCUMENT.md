# Banking Anomaly Detection System - Final Solution Document

## 1. Executive Summary

The Banking Anomaly Detection System is a headless, high-performance API service designed for sub-100ms fraud detection. By eliminating the UI layer, the system is optimized for direct integration with core banking systems. It utilizes a Triple-Layer Defense (Business Rules + Machine Learning + Deep Learning) to analyze 43 distinct behavioral features per transaction.

---

## 2. System Architecture (The Headless Engine)

### 2.1 API-First Logic Flow

```
Request Ingestion
    ↓
Security Middleware (API Key, Rate Limits, Input Sanitization)
    ↓
Feature Enrichment (Fetch historical user data from MSSQL)
    ↓
Triple-Layer Evaluation:
  ├─ Layer 1 (Hard Rules): Velocity/Limit breaches
  ├─ Layer 2 (Isolation Forest): Statistical anomaly score
  └─ Layer 3 (Autoencoder): Behavioral deviation
    ↓
Hybrid Decision Engine (Aggregate scores)
    ↓
Persistence (Log to MSSQL)
    ↓
JSON Response
```

### 2.2 Core Technology Stack

- **Framework:** FastAPI (Asynchronous/Uvicorn)
- **Language:** Python 3.11+
- **Models:** Scikit-learn (Isolation Forest), TensorFlow/Keras (Autoencoder)
- **Database:** Microsoft SQL Server (MSSQL)
- **Data Serialization:** Pydantic (Strict Type Checking)
- **Caching:** Redis (optional) / In-Memory (fallback)

---

## 3. Data Engineering & 43 Features

### 3.1 Core Transaction Features

1. **txn_amount** - Transaction amount in AED
2. **flag_amount** - Indicates money sent abroad (1/0)
3. **transfer_type_encoded** - Numeric encoding (0-6)
4. **transfer_type_risk** - Risk score per transfer type (0-0.9)
5. **channel_encoded** - Channel type (0 = Mobile)

### 3.2 Transfer Type Risk Scores

| Transfer Type | Code | Risk Score | Category |
|--------------|------|-----------|----------|
| Overseas | S | 0.9 | Highest (cross-border, harder to trace) |
| Quick Remittance | Q | 0.5 | Medium (fast, less verification) |
| UAE Domestic | L | 0.2 | Low (within country, regulated) |
| Ajman Local | I | 0.1 | Very Low (local, easy to trace) |
| Own Account | O | 0.0 | No Risk (same customer, same bank) |
| Mobile Pay | M | 0.3 | Minimal (mobile payments) |
| Family Pay | F | 0.15 | Low (family account transfers) |

### 3.3 Transfer Type Encoding

- S (Overseas) = 4
- Q (Quick Remittance) = 3
- L (Within UAE) = 2
- I (Within Ajman) = 1
- O (Own Account) = 0
- M (MobilePay) = 5
- F (Family Pay) = 6

### 3.4 Temporal Features

6. **hour** - Hour of transaction (0-23)
7. **day_of_week** - Day of week (0-6)
8. **is_weekend** - Weekend flag (1/0)
9. **is_night** - Night transaction flag (10pm-6am) (1/0)
10. **time_since_last_txn** - Seconds since last transaction
11. **recent_burst** - Burst flag if < 300 seconds (1/0)
12. **txn_velocity** - Transactions per hour rate

### 3.5 User Behavioral Features

13. **user_avg_amount** - Historical average transaction amount
14. **user_std_amount** - Standard deviation of historical amounts
15. **user_max_amount** - User's maximum transaction amount
16. **user_txn_frequency** - Total historical transactions count
17. **deviation_from_avg** - Difference from user average
18. **amount_to_max_ratio** - Amount / User max ratio
19. **intl_ratio** - International transactions / Total transactions
20. **user_high_risk_txn_ratio** - High-risk txns / Total txns

### 3.6 Account & Relationship Features

21. **num_accounts** - Total accounts per customer
22. **user_multiple_accounts_flag** - Multiple accounts flag (1/0)
23. **cross_account_transfer_ratio** - Cross-account txns / Total txns
24. **geo_anomaly_flag** - Unique countries > 2 (1/0)
25. **is_new_beneficiary** - New beneficiary flag (1/0)
26. **beneficiary_txn_count_30d** - Transactions to beneficiary in 30 days

### 3.7 Velocity & Frequency Features

27. **txn_count_30s** - Transactions in 30 seconds
28. **txn_count_10min** - Transactions in 10 minutes
29. **txn_count_1hour** - Transactions in 1 hour
30. **hourly_total** - Sum of transactions in 1 hour
31. **hourly_count** - Count of transactions in 1 hour
32. **daily_total** - Sum of transactions in 1 day
33. **daily_count** - Count of transactions in 1 day

### 3.8 Advanced Analytical Features

34. **weekly_total** - Sum of transactions in 1 week
35. **weekly_txn_count** - Count of transactions in 1 week
36. **weekly_avg_amount** - Average transaction amount in 1 week
37. **weekly_deviation** - Deviation from weekly average
38. **amount_vs_weekly_avg** - Transaction amount / Weekly average
39. **current_month_spending** - Sum of transactions in current month
40. **monthly_txn_count** - Count of transactions in current month
41. **monthly_avg_amount** - Average transaction amount in current month
42. **monthly_deviation** - Deviation from monthly average
43. **amount_vs_monthly_avg** - Transaction amount / Monthly average

### 3.9 Volatility Features

44. **rolling_std** - Standard deviation of last 5 transactions
45. **user_high_risk_txn_ratio** - Ratio of high-risk transfer types

---

## 4. Configuration Management System

### 4.1 Three-Layer Configuration

```
Layer 1: Static Config (File)
├── risk_thresholds.json
└── .env

Layer 2: Global Config (Database)
├── FeaturesConfig (47 features/rules)
└── ThresholdConfig (23 thresholds)

Layer 3: Customer-Specific Config (Database)
└── CustomerAccountTransferTypeConfig (overrides)
```

### 4.2 Database Tables for Configuration

#### FeaturesConfig Table
- **Purpose:** Enable/disable 47 ML features globally
- **Columns:** FeatureID, FeatureName, Description, IsEnabled, FeatureType, Version, CreatedAt, UpdatedAt, CreatedBy, UpdatedBy, RollbackVersion, IsActive
- **Data:** 43 ML Features + 4 Rule Checks

#### ThresholdConfig Table
- **Purpose:** Store all global threshold values
- **Columns:** ThresholdID, ThresholdName, ThresholdType, ThresholdValue, MinValue, MaxValue, PreviousValue, Description, IsActive, EffectiveFrom, EffectiveTo, CreatedAt, UpdatedAt, CreatedBy, UpdatedBy, Rationale, ImpactAnalysis, ApprovalStatus, ApprovedBy
- **Data:** 23 Thresholds (Isolation Forest, Confidence, Velocity, Transfer Multipliers, Transfer Floors)

#### CustomerAccountTransferTypeConfig Table
- **Purpose:** Override global config for specific customers
- **Columns:** ConfigID, CustomerID, AccountNo, TransferType, ParameterName, ParameterValue, IsEnabled, DataType, MinValue, MaxValue, Description, CreatedAt, UpdatedAt, CreatedBy, UpdatedBy, IsActive
- **Unique Constraint:** (CustomerID, AccountNo, TransferType, ParameterName)

### 4.3 Configuration Priority (Hierarchy)

```
1. Check CustomerAccountTransferTypeConfig
   ├─ If found → Use this value
   └─ If not found → Go to step 2

2. Check FeaturesConfig / ThresholdConfig
   ├─ If found → Use this value
   └─ If not found → Go to step 3

3. Use Default / File Value
   └─ Use risk_thresholds.json or hardcoded default
```

### 4.4 Real-Time ON/OFF Management

**Global (All Customers):**
```sql
UPDATE FeaturesConfig
SET IsEnabled = 0
WHERE FeatureName = 'velocity_check_10min'
```

**Customer-Specific:**
```sql
INSERT INTO CustomerAccountTransferTypeConfig
(CustomerID, AccountNo, TransferType, ParameterName, ParameterValue, IsEnabled, CreatedBy)
VALUES
('1060284', '011060284018', 'O', 'velocity_check_10min', 'OFF', 0, 'ADMIN')
```

---

## 5. Database Tables & Data Flow

### 5.1 Table 1: TransactionHistoryLogs (Source Data)

**Purpose:** Original transaction data from banking system

**Data Flow:**
```
User sends transaction
    ↓
API receives request
    ↓
Query TransactionHistoryLogs
    ↓
Calculate user statistics (avg, std, max)
```

### 5.2 Table 2: FeaturesConfig (Global Feature Toggles)

**Purpose:** Enable/disable 47 ML features globally

**Data Flow:**
```
Feature Engineering starts
    ↓
Check FeaturesConfig
    ↓
For each feature:
  - If IsEnabled = 1 → Include
  - If IsEnabled = 0 → Skip
    ↓
Build feature vector
```

### 5.3 Table 3: ThresholdConfig (Global Thresholds)

**Purpose:** Store all global threshold values

**Data Flow:**
```
Rule Engine starts
    ↓
Query ThresholdConfig
    ↓
Get transfer multipliers & floors
    ↓
Calculate threshold
```

### 5.4 Table 4: CustomerAccountTransferTypeConfig (Customer Overrides)

**Purpose:** Override global config for specific customers

**Data Flow:**
```
Transaction arrives
    ↓
Query CustomerAccountTransferTypeConfig
    ↓
If found → Use customer config
Else → Use global config
```

### 5.5 Table 5: APITransactionLogs (API Transactions & Idempotence)

**Purpose:** Log all API transactions for idempotence and audit trail

**Columns:** LogID, IdempotenceKey, RequestTimestamp, ResponseTimestamp, ExecutionTimeMs, RequestMethod, RequestEndpoint, RequestPayload, RequestHeaders, ResponsePayload, ResponseStatusCode, APIKeyUsed, UserID, SessionID, IsSuccessful, ErrorCode, ErrorMessage, StackTrace, ClientIP, UserAgent, RetryCount, IsRetry, OriginalLogID, TransactionID, RiskScore, Decision, CreatedAt, DataClassification

**Data Flow:**
```
API receives request
    ↓
Generate IdempotenceKey
    ↓
Check APITransactionLogs
    ↓
If exists → Return cached response
Else → Process & store
```

### 5.6 Table 6: PendingTransactions (Manual Review Queue)

**Purpose:** Store transactions requiring user approval

**Data Flow:**
```
Fraud detection completes
    ↓
Risk Level = HIGH/MEDIUM?
    ↓
Yes → Insert into PendingTransactions
No → Auto-approve/reject
```

### 5.7 Complete Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    API Request Received                         │
│              (customer_id, account_no, amount, etc.)            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │  Check APITransactionLogs          │
        │  (Idempotence Check)               │
        │  If duplicate → Return cached      │
        └────────────────┬───────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │  Query TransactionHistoryLogs      │
        │  Get user's historical data        │
        └────────────────┬───────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │  Query FeaturesConfig              │
        │  Get enabled features list         │
        └────────────────┬───────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │  Feature Engineering               │
        │  Build 43 features                 │
        └────────────────┬───────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │  Query ThresholdConfig             │
        │  Get transfer multipliers & floors │
        └────────────────┬───────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │  Query CustomerAccountTransferType │
        │  Get customer-specific overrides   │
        └────────────────┬───────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │  Rule Engine                       │
        │  Check velocity, spending, etc.    │
        └────────────────┬───────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │  ML Models                         │
        │  Isolation Forest + Autoencoder    │
        └────────────────┬───────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │  Hybrid Decision                   │
        │  Combine all signals               │
        │  Calculate risk score              │
        └────────────────┬───────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │  Insert APITransactionLogs         │
        │  Store decision & details          │
        └────────────────┬───────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │  Risk Level = HIGH/MEDIUM?         │
        └────────────────┬───────────────────┘
                    ┌────┴────┐
                    │          │
                   YES        NO
                    │          │
                    ▼          ▼
        ┌──────────────────┐  ┌──────────────────┐
        │ Insert into      │  │ Auto-approve or  │
        │ PendingTxns      │  │ Auto-reject      │
        │ Status=pending   │  │                  │
        └──────────────────┘  └──────────────────┘
                    │          │
                    └────┬─────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │  Return Response                   │
        │  (is_fraud, risk_score, reasons)   │
        └────────────────────────────────────┘
```

---

## 6. Risk Score System

### 6.1 What is Risk Score?

Risk Score (0 to 1.0) represents transaction fraud probability:
- **0.0** = Completely safe
- **0.5** = Medium risk
- **1.0** = Maximum risk (definitely fraud)

### 6.2 Risk Score Calculation

```
Final Risk Score = Rule Engine Score + ML Score + AE Score
                 = (0-0.85) + (0-0.15) + (0-0.10)
                 = 0 to 1.0
```

**Base Scores per Violation Type:**
- Velocity Violation → 0.85
- Monthly Spending Violation → 0.70
- New Beneficiary → 0.60
- Other Violations → 0.75
- No Violations → 0.00

### 6.3 Risk Level Classification

```
Risk Score >= 0.8   → HIGH RISK → REQUIRES_USER_APPROVAL
Risk Score >= 0.65  → MEDIUM RISK → REQUIRES_USER_APPROVAL
Risk Score >= 0.4   → LOW RISK → APPROVE_WITH_NOTIFICATION
Risk Score < 0.4    → SAFE → APPROVED
```

### 6.4 Confidence Level

```
Models Agreeing    Confidence
3 (All)           95%
2                 80%
1                 60%
0                 60%

+ High Risk Boost: +3% if ML score > 0.8
```

### 6.5 Model Agreement

```
Model Agreement = (Rule Flagged + ML Flagged + AE Flagged) / 3
```

---

## 7. API Endpoint Specifications

### 7.1 Core Inference

**POST /api/analyze-transaction**

**Purpose:** Real-time fraud detection

**Request:**
```json
{
  "customer_id": "1060284",
  "from_account_no": "011060284018",
  "to_account_no": "501004978587611060284",
  "transaction_amount": 50000,
  "transfer_type": "O",
  "bank_country": "UAE",
  "idempotence_key": "unique-key-123"
}
```

**Response:**
```json
{
  "transaction_id": "TXN_99283",
  "decision": "FLAGGED",
  "risk_score": 0.84,
  "risk_level": "HIGH",
  "confidence_level": 0.95,
  "model_agreement": 0.67,
  "reasons": [
    "Velocity limit exceeded: 8 transactions in last 10 minutes",
    "ML anomaly detected: risk score 0.85 exceeds threshold 0.65"
  ],
  "individual_scores": {
    "rule_engine": {"violated": true, "threshold": 45000},
    "isolation_forest": {"anomaly_score": 0.85, "is_anomaly": true},
    "autoencoder": {"reconstruction_error": 0.12, "is_anomaly": false}
  },
  "processing_time_ms": 87,
  "idempotence_key": "unique-key-123",
  "is_cached": false
}
```

### 7.2 Administrative Control

**POST /api/config/thresholds**
- Update risk sensitivity without downtime

**POST /api/config/features/toggle**
- Enable/disable specific features

**GET /api/logs/audit**
- Retrieve historical decision logs for compliance

---

## 8. Implementation Timeline

### Phase 1: Environment (1 Hour)
- MSSQL Database setup and schema execution
- Python environment & dependency installation

### Phase 2: Model & Logic (1.5-2 Hours)
- Integration of rule_engine.py
- Loading .pkl and .h5 model files
- Feature engineering pipeline

### Phase 3: API & Security (1.5-2 Hours)
- FastAPI endpoint development
- API Key and Basic Auth middleware
- Pydantic model validation

### Phase 4: Testing & Deployment (1.5 Hours)
- Latency testing (< 100ms target)
- Uvicorn production server configuration

---

## 9. Security & Compliance

### 9.1 Authentication
- API calls must include X-API-Key header
- Basic Auth for admin endpoints

### 9.2 Data Integrity
- All model files verified with SHA-256 hashes on startup
- Idempotence keys prevent duplicate processing

### 9.3 Auditability
- Every decision traceable to specific model version
- Complete audit trail in APITransactionLogs
- Configuration changes tracked with CreatedBy/UpdatedBy

### 9.4 Performance
- Target latency: < 100ms per transaction
- Throughput: 1000+ transactions/second
- Connection pooling for database

---

## 10. Monitoring & Metrics

### 10.1 Performance Metrics
- **Latency:** < 500ms per transaction
- **Throughput:** 1000+ transactions/second
- **Accuracy:** Depends on model training data

### 10.2 Fraud Detection Metrics
- **True Positive Rate (TPR):** % of actual fraud caught
- **False Positive Rate (FPR):** % of legitimate flagged as fraud
- **Precision:** % of flagged transactions that are actually fraud
- **Recall:** % of actual fraud that was detected

### 10.3 System Health
- **API Uptime:** 99.9%
- **DB Connection:** Active
- **Model Load Status:** All models loaded

---

## 11. Future Enhancements

1. Real-time model retraining
2. Feedback loop from approved/rejected transactions
3. Geographic analysis improvements
4. Device fingerprinting
5. Network analysis for fraud rings
6. SHAP values for explainability

---

## Conclusion

This Banking Anomaly Detection System provides:
- Real-time fraud detection (< 100ms)
- Triple-layer defense mechanism
- Database-driven dynamic configuration
- Complete audit trail and compliance
- Production-ready architecture
- Banking-grade security

System is fully operational and ready for deployment.
