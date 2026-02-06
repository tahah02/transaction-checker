# Comprehensive Automated Model Retraining Pipeline - Implementation Plan

## 📋 Executive Summary

**Objective:** Implement automated weekly/monthly model retraining with A/B testing, versioning, and rollback capabilities

**Data Sources:**
- `TransactionHistoryLogs` - Historical baseline data
- `APITransactionLogs` - Recent user behavior and labeled transactions

**Key Features:**
- Automated scheduled retraining (weekly/monthly)
- A/B testing framework for model validation
- Semantic versioning with rollback capabilities
- Real-time performance monitoring
- Data/model drift detection
- Zero-downtime deployment

---

## 🏗️ 1. Project Structure

```
project/
├── mlops/
│   ├── __init__.py
│   │
│   ├── training/
│   │   ├── __init__.py
│   │   ├── data_preparation.py       # Fetch from both tables + merge
│   │   ├── model_trainer.py          # Train IF + Autoencoder
│   │   └── train_pipeline.py         # Main orchestrator
│   │
│   ├── validation/
│   │   ├── __init__.py
│   │   ├── metrics_calculator.py     # Precision, Recall, F1, FPR
│   │   ├── model_validator.py        # Validation logic
│   │   └── ab_testing.py             # A/B test framework
│   │
│   ├── versioning/
│   │   ├── __init__.py
│   │   ├── model_registry.py         # Version tracking + metadata
│   │   └── rollback_manager.py       # Rollback to previous version
│   │
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── drift_detector.py         # Data/model drift detection
│   │   └── performance_tracker.py    # Real-time metrics logging
│   │
│   └── scheduler/
│       ├── __init__.py
│       ├── cron_scheduler.py         # APScheduler setup
│       └── trigger_manager.py        # Manual/auto triggers
│
├── backend/
│   ├── model_versions/               # Versioned models storage
│   │   ├── v1.0.0/
│   │   │   ├── isolation_forest.pkl
│   │   │   ├── autoencoder.h5
│   │   │   ├── isolation_forest_scaler.pkl
│   │   │   ├── autoencoder_scaler.pkl
│   │   │   └── metadata.json
│   │   ├── v1.1.0/
│   │   ├── v1.2.0/
│   │   └── current -> v1.0.0         # Symlink to active version
│   │
│   └── (existing files...)
│
└── api/
    └── mlops_api.py                  # New MLOps endpoints
```

---

## 🗄️ 2. Database Schema Updates

### 2.1 ModelVersions Table

```sql
CREATE TABLE ModelVersions (
    VersionId VARCHAR(50) PRIMARY KEY,           -- e.g., 'v1.0.0', 'v1.1.0'
    ModelType VARCHAR(50),                       -- 'isolation_forest' or 'autoencoder'
    CreatedAt DATETIME DEFAULT GETDATE(),
    TrainingDataSize INT,                        -- Total records used
    HistoricalRecords INT,                       -- From TransactionHistoryLogs
    RecentRecords INT,                           -- From APITransactionLogs
    Metrics NVARCHAR(MAX),                       -- JSON: {precision, recall, f1, fpr, accuracy}
    IsActive BIT DEFAULT 0,                      -- Currently deployed?
    FilePath VARCHAR(255),                       -- Path to model file
    TrainingDuration INT,                        -- Training time in seconds
    HyperParameters NVARCHAR(MAX),               -- JSON: model hyperparameters
    DataDateRange VARCHAR(100),                  -- e.g., '2024-01-01 to 2024-12-31'
    CreatedBy VARCHAR(50)                        -- 'scheduler', 'manual', 'drift_trigger'
);
```

### 2.2 ABTestResults Table

```sql
CREATE TABLE ABTestResults (
    TestId VARCHAR(50) PRIMARY KEY,              -- e.g., 'ab_test_20240201_001'
    ChampionVersion VARCHAR(50),                 -- Current production model
    ChallengerVersion VARCHAR(50),               -- New candidate model
    StartDate DATETIME,
    EndDate DATETIME,
    TrafficSplit VARCHAR(20),                    -- e.g., '80/20'
    ChampionMetrics NVARCHAR(MAX),               -- JSON: performance metrics
    ChallengerMetrics NVARCHAR(MAX),             -- JSON: performance metrics
    TotalTransactions INT,
    ChampionTransactions INT,
    ChallengerTransactions INT,
    Winner VARCHAR(50),                          -- 'champion', 'challenger', or 'no_winner'
    PromotedAt DATETIME,
    StatisticalSignificance FLOAT,               -- p-value
    Notes NVARCHAR(500)
);
```

### 2.3 ModelPerformanceLogs Table

```sql
CREATE TABLE ModelPerformanceLogs (
    LogId INT IDENTITY(1,1) PRIMARY KEY,
    VersionId VARCHAR(50),
    Timestamp DATETIME DEFAULT GETDATE(),
    TransactionId VARCHAR(50),
    Prediction VARCHAR(20),                      -- 'APPROVE', 'REVIEW', 'REJECT'
    ActualLabel VARCHAR(20),                     -- After user action
    IsCorrect BIT,                               -- Prediction == Actual?
    RiskScore FLOAT,
    ProcessingTimeMs INT,
    ABTestId VARCHAR(50)                         -- NULL if not in A/B test
);
```

### 2.4 TrainingHistory Table

```sql
CREATE TABLE TrainingHistory (
    TrainingId VARCHAR(50) PRIMARY KEY,
    VersionId VARCHAR(50),
    StartTime DATETIME,
    EndTime DATETIME,
    Status VARCHAR(20),                          -- 'SUCCESS', 'FAILED', 'RUNNING'
    ErrorMessage NVARCHAR(MAX),
    TriggeredBy VARCHAR(50),                     -- 'scheduler', 'manual', 'drift_detected'
    DataFetchTime INT,                           -- Seconds
    FeatureEngineeringTime INT,                  -- Seconds
    ModelTrainingTime INT,                       -- Seconds
    TotalRecords INT,
    HistoricalRecords INT,
    RecentRecords INT
);
```

### 2.5 DriftDetectionLogs Table

```sql
CREATE TABLE DriftDetectionLogs (
    DriftId INT IDENTITY(1,1) PRIMARY KEY,
    DetectionDate DATETIME DEFAULT GETDATE(),
    DriftType VARCHAR(50),                       -- 'data_drift', 'model_drift'
    FeatureName VARCHAR(100),                    -- NULL for model drift
    PSI_Score FLOAT,                             -- Population Stability Index
    Threshold FLOAT,
    IsDriftDetected BIT,
    ActionTaken VARCHAR(100),                    -- 'retraining_triggered', 'alert_sent', 'none'
    Notes NVARCHAR(500)
);
```

---

## 🔧 3. Core Components

### 3.1 Data Preparation Module
**File:** `mlops/training/data_preparation.py`


**Key Functions:**
```python
fetch_historical_data()              # Fetch ALL from TransactionHistoryLogs
fetch_recent_data(since_date)        # Fetch NEW from APITransactionLogs
merge_datasets(df1, df2)             # Combine + deduplicate
balance_classes(df)                  # Handle imbalanced data (SMOTE/undersampling)
apply_feature_engineering(df)        # Use existing feature_engineering.py
prepare_training_data()              # Main orchestrator function
```

**Data Fetching Logic:**
1. **Historical Data (TransactionHistoryLogs):**
   - Fetch ALL records (baseline)
   - Provides stable foundation

2. **Recent Data (APITransactionLogs):**
   - Fetch WHERE `CreatedAt > last_training_date`
   - AND `UserAction IN ('APPROVED', 'REJECTED')` (labeled data only)
   - Captures recent user behavior changes

3. **Merge Strategy:**
   - Combine both datasets
   - Remove duplicates (if any)
   - Balance fraud/non-fraud classes
   - Apply feature engineering
   - Split: 80% train, 20% validation

---

### 3.2 Model Trainer Module
**File:** `mlops/training/model_trainer.py`

**Key Functions:**
```python
train_isolation_forest(X_train, y_train)
train_autoencoder(X_train)
evaluate_model(model, X_test, y_test)
save_model_with_version(model, version_id, model_type)
save_metadata(version_id, metrics, data_stats)
train_both_models()                  # Main function
```

**Training Process:**
1. Train Isolation Forest (reuse logic from `train_isolation_forest.py`)
2. Train Autoencoder (reuse logic from `train_autoencoder.py`)
3. Evaluate on validation set
4. Save models in `backend/model_versions/v1.x.x/`
5. Save metadata.json with metrics
6. Log to `ModelVersions` table

---

### 3.3 Training Pipeline Module
**File:** `mlops/training/train_pipeline.py`


**Main Orchestrator Function:**
```python
def run_training_pipeline(triggered_by='scheduler'):
    # Step 1: Get last training date
    last_training_date = get_last_training_date()
    
    # Step 2: Fetch & prepare data
    X_train, X_val, y_train, y_val = prepare_training_data(last_training_date)
    
    # Step 3: Train models
    models = train_both_models(X_train, y_train)
    
    # Step 4: Validate
    metrics = evaluate_models(models, X_val, y_val)
    
    # Step 5: Generate version ID
    version_id = generate_version_id()  # e.g., v1.1.0
    
    # Step 6: Save models + metadata
    save_models_with_version(models, version_id, metrics)
    
    # Step 7: Log to database
    log_training_history(version_id, metrics, triggered_by)
    
    # Step 8: Optionally trigger A/B test
    if metrics['f1_score'] > current_model_f1:
        trigger_ab_test(current_version, version_id)
    
    return version_id, metrics
```

---

### 3.4 Model Registry Module
**File:** `mlops/versioning/model_registry.py`

**Key Functions:**
```python
register_model(version_id, metadata)
get_active_version()
get_all_versions()
activate_version(version_id)
deactivate_version(version_id)
get_version_metadata(version_id)
compare_versions(version1, version2)
```

**Responsibilities:**
- Track all model versions in database
- Manage active/inactive status
- Provide version comparison
- Store and retrieve metadata

---

### 3.5 A/B Testing Framework
**File:** `mlops/validation/ab_testing.py`


**Key Functions:**
```python
start_ab_test(champion_version, challenger_version, duration_days=7, split='80/20')
route_traffic(transaction)           # Decide which model to use
log_prediction(test_id, version, prediction, actual, transaction_id)
calculate_test_metrics(test_id)
determine_winner(test_id)            # Statistical significance test
end_ab_test(test_id)
promote_challenger(test_id)
```

**A/B Testing Flow:**
1. **Start Test:**
   - Champion: Current production model (v1.0.0)
   - Challenger: New candidate model (v1.1.0)
   - Duration: 7 days
   - Split: 80% champion, 20% challenger

2. **Traffic Routing:**
   - Random assignment based on split ratio
   - Log which model was used for each transaction

3. **Metrics Collection:**
   - Track predictions from both models
   - Wait for user actions (APPROVED/REJECTED)
   - Calculate: Precision, Recall, F1, FPR, Accuracy

4. **Winner Determination:**
   - Compare metrics after test duration
   - Chi-square test for statistical significance
   - If challenger wins: Promote to production
   - If champion wins: Keep current model

5. **Promotion:**
   - Update `current` symlink
   - Mark challenger as active in database
   - Deactivate champion
   - Log to ABTestResults table

---

### 3.6 Rollback Manager
**File:** `mlops/versioning/rollback_manager.py`

**Key Functions:**
```python
rollback_to_version(version_id, reason)
get_rollback_history()
auto_rollback_on_performance_drop(threshold=0.05)
update_symlink(version_id)
restart_api_gracefully()
```

**Rollback Scenarios:**
1. **Manual Rollback:** Admin triggers via API
2. **Auto Rollback:** Performance drops > 5%
3. **Emergency Rollback:** Critical bug detected

**Rollback Process:**
1. Validate target version exists
2. Update `current` symlink to target version
3. Mark target version as active
4. Deactivate current version
5. Restart API (graceful reload)
6. Log rollback event
7. Send notification

---

### 3.7 Drift Detector
**File:** `mlops/monitoring/drift_detector.py`


**Key Functions:**
```python
detect_data_drift()                  # Feature distribution changes
detect_model_drift()                 # Performance degradation
calculate_psi(expected, actual)      # Population Stability Index
trigger_retraining_if_needed()
```

**Drift Detection Logic:**

1. **Data Drift (Feature Distribution):**
   - Compare current feature distributions with training data
   - Calculate PSI (Population Stability Index) for each feature
   - PSI > 0.2: Significant drift detected
   - Action: Trigger retraining

2. **Model Drift (Performance Degradation):**
   - Monitor weekly F1 score, Precision, Recall
   - Compare with baseline metrics
   - If drop > 5%: Drift detected
   - Action: Trigger retraining

3. **Monitoring Schedule:**
   - Run daily at 3 AM
   - Check last 7 days of data
   - Log to DriftDetectionLogs table

---

### 3.8 Scheduler Module
**File:** `mlops/scheduler/cron_scheduler.py`

**Using APScheduler:**
```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

# Weekly retraining: Every Monday at 2 AM
scheduler.add_job(
    run_training_pipeline,
    trigger='cron',
    day_of_week='mon',
    hour=2,
    minute=0,
    args=['scheduler']
)

# Monthly retraining: 1st of month at 2 AM
scheduler.add_job(
    run_training_pipeline,
    trigger='cron',
    day=1,
    hour=2,
    minute=0,
    args=['scheduler']
)

# Drift detection: Daily at 3 AM
scheduler.add_job(
    detect_drift,
    trigger='cron',
    hour=3,
    minute=0
)

scheduler.start()
```

**Trigger Types:**
1. **Scheduled:** Weekly/Monthly cron jobs
2. **Manual:** API endpoint trigger
3. **Drift-based:** Auto trigger when drift detected
4. **Performance-based:** Auto trigger on performance drop

---

## 🔄 4. Complete End-to-End Flow

### 4.1 Complete System Flow Diagram

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    AUTOMATED MODEL RETRAINING - COMPLETE FLOW                  ║
╚═══════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: INITIAL STATE (Current Production)                                 │
└─────────────────────────────────────────────────────────────────────────────┘

    Production Model: v1.0.0
    ├── Trained: 3 months ago
    ├── Data: TransactionHistoryLogs (50,000 records)
    ├── Metrics: F1=0.85, Precision=0.87, Recall=0.83
    └── Status: Active, serving 100% traffic

    Database Tables:
    ├── TransactionHistoryLogs: 50,000 historical records
    └── APITransactionLogs: Growing daily with new transactions


┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 2: SCHEDULED TRIGGER (Every Monday 2:00 AM)                           │
└─────────────────────────────────────────────────────────────────────────────┘

    ⏰ Monday, 2:00 AM - Cron Job Triggers
    
    mlops/scheduler/cron_scheduler.py
    └── Executes: run_training_pipeline(triggered_by='scheduler')


┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 3: DATA PREPARATION                                                   │
└─────────────────────────────────────────────────────────────────────────────┘

    Step 3.1: Get Last Training Date
    ├── Query ModelVersions table
    ├── Find: v1.0.0 trained on 2024-11-01
    └── Last training date: 2024-11-01

    Step 3.2: Fetch Historical Data
    ├── Source: TransactionHistoryLogs
    ├── Query: SELECT * FROM TransactionHistoryLogs
    ├── Records: 50,000
    └── Columns: CustomerId, Amount, TransferType, CreateDate, etc.

    Step 3.3: Fetch Recent Data
    ├── Source: APITransactionLogs
    ├── Query: SELECT * FROM APITransactionLogs 
    │          WHERE CreatedAt > '2024-11-01'
    │          AND UserAction IN ('APPROVED', 'REJECTED')
    ├── Records: 2,500 (new labeled transactions)
    └── Why: Capture recent user behavior changes

    Step 3.4: Merge Datasets
    ├── Combine: 50,000 + 2,500 = 52,500 total records
    ├── Remove duplicates (if any)
    ├── Check data quality
    └── Result: 52,500 clean records

    Step 3.5: Feature Engineering
    ├── Apply: backend/feature_engineering.py
    ├── Generate features:
    │   ├── transaction_amount
    │   ├── user_avg_amount
    │   ├── user_std_amount
    │   ├── amount_deviation
    │   ├── time_since_last_txn
    │   ├── txn_count_10min
    │   ├── is_new_beneficiary
    │   └── 50+ more features
    └── Result: Feature matrix (52,500 × 60)

    Step 3.6: Balance Classes
    ├── Fraud: 2,100 (4%)
    ├── Normal: 50,400 (96%)
    ├── Apply: SMOTE or undersampling
    └── Result: Balanced dataset

    Step 3.7: Train-Validation Split
    ├── Train: 42,000 (80%)
    └── Validation: 10,500 (20%)


┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 4: MODEL TRAINING                                                     │
└─────────────────────────────────────────────────────────────────────────────┘

    Step 4.1: Train Isolation Forest
    ├── Algorithm: Isolation Forest
    ├── Hyperparameters:
    │   ├── n_estimators: 100
    │   ├── contamination: 0.04
    │   └── random_state: 42
    ├── Training time: 120 seconds
    └── Output: isolation_forest.pkl

    Step 4.2: Train Autoencoder
    ├── Architecture:
    │   ├── Input: 60 features
    │   ├── Encoder: [60 → 30 → 15 → 8]
    │   ├── Decoder: [8 → 15 → 30 → 60]
    │   └── Loss: MSE
    ├── Training:
    │   ├── Epochs: 50
    │   ├── Batch size: 32
    │   └── Early stopping: Yes
    ├── Training time: 240 seconds
    └── Output: autoencoder.h5

    Step 4.3: Evaluate on Validation Set
    ├── Isolation Forest:
    │   ├── Precision: 0.89
    │   ├── Recall: 0.86
    │   ├── F1: 0.875
    │   └── FPR: 0.06
    ├── Autoencoder:
    │   ├── Precision: 0.91
    │   ├── Recall: 0.85
    │   ├── F1: 0.88
    │   └── FPR: 0.05
    └── Combined (Hybrid):
        ├── Precision: 0.92
        ├── Recall: 0.88
        ├── F1: 0.90
        └── FPR: 0.04


┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 5: VERSION MANAGEMENT                                                 │
└─────────────────────────────────────────────────────────────────────────────┘

    Step 5.1: Generate Version ID
    ├── Current: v1.0.0
    ├── New: v1.1.0 (minor version bump)
    └── Reason: Scheduled retraining

    Step 5.2: Save Models
    ├── Directory: backend/model_versions/v1.1.0/
    ├── Files:
    │   ├── isolation_forest.pkl
    │   ├── isolation_forest_scaler.pkl
    │   ├── autoencoder.h5
    │   ├── autoencoder_scaler.pkl
    │   └── metadata.json
    └── Metadata.json:
        {
          "version": "v1.1.0",
          "created_at": "2024-02-05 02:15:00",
          "training_data_size": 52500,
          "historical_records": 50000,
          "recent_records": 2500,
          "metrics": {
            "f1_score": 0.90,
            "precision": 0.92,
            "recall": 0.88,
            "fpr": 0.04
          },
          "training_duration": 360,
          "triggered_by": "scheduler"
        }

    Step 5.3: Register in Database
    ├── Table: ModelVersions
    ├── INSERT:
    │   ├── VersionId: 'v1.1.0'
    │   ├── ModelType: 'hybrid'
    │   ├── CreatedAt: '2024-02-05 02:15:00'
    │   ├── Metrics: JSON
    │   ├── IsActive: 0 (not yet active)
    │   └── FilePath: 'backend/model_versions/v1.1.0/'
    └── Status: Registered

    Step 5.4: Log Training History
    ├── Table: TrainingHistory
    └── INSERT:
        ├── TrainingId: 'train_20240205_001'
        ├── VersionId: 'v1.1.0'
        ├── Status: 'SUCCESS'
        ├── TriggeredBy: 'scheduler'
        └── TotalRecords: 52500


┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 6: MODEL COMPARISON & DECISION                                        │
└─────────────────────────────────────────────────────────────────────────────┘

    Step 6.1: Compare Metrics
    
    ┌─────────────────┬──────────┬──────────┬────────────┐
    │ Metric          │ v1.0.0   │ v1.1.0   │ Improvement│
    ├─────────────────┼──────────┼──────────┼────────────┤
    │ F1 Score        │ 0.85     │ 0.90     │ +5.9%      │
    │ Precision       │ 0.87     │ 0.92     │ +5.7%      │
    │ Recall          │ 0.83     │ 0.88     │ +6.0%      │
    │ FPR             │ 0.08     │ 0.04     │ -50%       │
    └─────────────────┴──────────┴──────────┴────────────┘

    Step 6.2: Decision Logic
    ├── IF new_f1 > current_f1 + 0.02 (2% improvement threshold)
    │   └── ✅ v1.1.0 is significantly better
    │       └── Trigger A/B Test
    ├── ELSE IF new_f1 > current_f1
    │   └── ⚠️ v1.1.0 is slightly better
    │       └── Optional: Manual review or direct A/B test
    └── ELSE
        └── ❌ v1.1.0 is not better
            └── Keep v1.0.0, log result, no deployment

    Step 6.3: Decision Result
    └── ✅ v1.1.0 shows 5.9% improvement → Proceed to A/B Test


┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 7: A/B TESTING SETUP                                                  │
└─────────────────────────────────────────────────────────────────────────────┘

    Step 7.1: Initialize A/B Test
    ├── Test ID: 'ab_test_20240205_001'
    ├── Champion: v1.0.0 (current production)
    ├── Challenger: v1.1.0 (new model)
    ├── Duration: 7 days
    ├── Traffic Split: 80/20
    └── Start Date: 2024-02-05 02:30:00

    Step 7.2: Register in Database
    ├── Table: ABTestResults
    └── INSERT:
        ├── TestId: 'ab_test_20240205_001'
        ├── ChampionVersion: 'v1.0.0'
        ├── ChallengerVersion: 'v1.1.0'
        ├── StartDate: '2024-02-05 02:30:00'
        ├── EndDate: '2024-02-12 02:30:00'
        ├── TrafficSplit: '80/20'
        └── Winner: NULL (pending)

    Step 7.3: Load Both Models in Memory
    ├── Champion (v1.0.0):
    │   ├── Load from: backend/model_versions/v1.0.0/
    │   └── Status: Ready
    └── Challenger (v1.1.0):
        ├── Load from: backend/model_versions/v1.1.0/
        └── Status: Ready


┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 8: A/B TESTING - LIVE TRAFFIC (7 Days)                               │
└─────────────────────────────────────────────────────────────────────────────┘

    🔄 For Each Incoming Transaction:

    Step 8.1: Transaction Arrives
    ├── POST /api/v1/transaction/predict
    ├── Request:
    │   ├── customer_id: "CUST12345"
    │   ├── amount: 15000
    │   ├── transfer_type: "S"
    │   └── ... other fields
    └── Transaction ID: "TXN_20240205_12345"

    Step 8.2: Traffic Routing Decision
    ├── Check: Is A/B test active?
    │   └── ✅ Yes: ab_test_20240205_001
    ├── Generate random number: 0.0 to 1.0
    │   └── Random: 0.65
    ├── Route Logic:
    │   ├── IF random < 0.80 → Champion (v1.0.0)
    │   └── ELSE → Challenger (v1.1.0)
    └── Decision: 0.65 < 0.80 → Use Champion (v1.0.0)

    Step 8.3: Make Prediction
    ├── Model: v1.0.0 (Champion)
    ├── Input: Feature vector (60 features)
    ├── Prediction:
    │   ├── Decision: "REQUIRES_USER_APPROVAL"
    │   ├── Risk Score: 0.72
    │   ├── Risk Level: "MEDIUM"
    │   └── Reasons: ["High amount deviation", "New beneficiary"]
    └── Processing Time: 45ms

    Step 8.4: Save to Database
    ├── Table: APITransactionLogs
    └── INSERT:
        ├── TransactionId: "TXN_20240205_12345"
        ├── Decision: "REQUIRES_USER_APPROVAL"
        ├── RiskScore: 0.72
        ├── ModelVersionUsed: "v1.0.0"          ← NEW COLUMN
        ├── ABTestId: "ab_test_20240205_001"    ← NEW COLUMN
        ├── ABTestGroup: "champion"             ← NEW COLUMN
        ├── UserAction: "PENDING"
        └── CreatedAt: "2024-02-05 10:30:00"

    Step 8.5: Return Response to User
    └── Response: {decision, risk_score, transaction_id, ...}

    Step 8.6: User Takes Action (Later)
    ├── User reviews transaction
    ├── Decision: APPROVED
    └── UPDATE APITransactionLogs:
        ├── UserAction: "APPROVED"
        ├── ActionedBy: "admin@bank.com"
        ├── ActionTimestamp: "2024-02-05 11:00:00"
        └── IsCorrectPrediction: 0 (model said REVIEW, user said APPROVE)

    📊 After 7 Days - Sample Statistics:

    Total Transactions: 10,000
    ├── Champion (v1.0.0): 8,000 transactions (80%)
    │   ├── Correct: 7,500
    │   ├── Wrong: 500
    │   └── Accuracy: 93.75%
    └── Challenger (v1.1.0): 2,000 transactions (20%)
        ├── Correct: 1,920
        ├── Wrong: 80
        └── Accuracy: 96.00%


┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 9: A/B TEST EVALUATION (Day 8)                                       │
└─────────────────────────────────────────────────────────────────────────────┘

    Step 9.1: Fetch Test Results
    ├── Query APITransactionLogs
    ├── WHERE ABTestId = 'ab_test_20240205_001'
    └── AND UserAction IN ('APPROVED', 'REJECTED')

    Step 9.2: Calculate Metrics

    Champion (v1.0.0) - 8,000 transactions:
    ├── True Positives: 320
    ├── False Positives: 480
    ├── True Negatives: 7,120
    ├── False Negatives: 80
    ├── Precision: 0.40 (320 / 800)
    ├── Recall: 0.80 (320 / 400)
    ├── F1 Score: 0.53
    └── FPR: 0.063 (480 / 7600)

    Challenger (v1.1.0) - 2,000 transactions:
    ├── True Positives: 90
    ├── False Positives: 60
    ├── True Negatives: 1,840
    ├── False Negatives: 10
    ├── Precision: 0.60 (90 / 150)
    ├── Recall: 0.90 (90 / 100)
    ├── F1 Score: 0.72
    └── FPR: 0.032 (60 / 1900)

    Step 9.3: Statistical Significance Test
    ├── Test: Chi-square test
    ├── Null Hypothesis: No difference between models
    ├── p-value: 0.001
    ├── Significance level: 0.05
    └── Result: p < 0.05 → Statistically significant difference

    Step 9.4: Determine Winner
    ├── Challenger F1 (0.72) > Champion F1 (0.53)
    ├── Challenger FPR (0.032) < Champion FPR (0.063)
    ├── Statistical significance: ✅ Confirmed
    └── 🏆 Winner: Challenger (v1.1.0)

    Step 9.5: Update Database
    ├── Table: ABTestResults
    └── UPDATE:
        ├── ChampionMetrics: JSON
        ├── ChallengerMetrics: JSON
        ├── Winner: 'challenger'
        ├── PromotedAt: '2024-02-12 03:00:00'
        └── StatisticalSignificance: 0.001


┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 10: MODEL PROMOTION (Zero Downtime)                                   │
└─────────────────────────────────────────────────────────────────────────────┘

    Step 10.1: Backup Current State
    ├── Log current version: v1.0.0
    ├── Save configuration
    └── Create rollback point

    Step 10.2: Update Symlink
    ├── Current: backend/model_versions/current → v1.0.0
    ├── Update: backend/model_versions/current → v1.1.0
    └── Status: Symlink updated

    Step 10.3: Update Database
    ├── Table: ModelVersions
    ├── UPDATE v1.0.0: SET IsActive = 0
    └── UPDATE v1.1.0: SET IsActive = 1

    Step 10.4: Reload Models (Graceful)
    ├── Load v1.1.0 models into memory
    ├── Wait for in-flight requests to complete
    ├── Switch to v1.1.0
    └── Unload v1.0.0 from memory

    Step 10.5: Verify Deployment
    ├── Test prediction endpoint
    ├── Check model version: v1.1.0 ✅
    ├── Test sample transactions
    └── All tests passed ✅

    Step 10.6: Send Notifications
    ├── Email: admin@bank.com
    ├── Subject: "Model v1.1.0 Promoted to Production"
    └── Body:
        - A/B test completed successfully
        - Challenger (v1.1.0) won with 96% accuracy
        - Model promoted at 2024-02-12 03:00:00
        - Rollback available if needed


┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 11: POST-DEPLOYMENT MONITORING                                        │
└─────────────────────────────────────────────────────────────────────────────┘

    🔍 Continuous Monitoring (24/7):

    Step 11.1: Performance Tracking
    ├── Table: ModelPerformanceLogs
    ├── Log every prediction
    └── Track:
        ├── Accuracy
        ├── Precision
        ├── Recall
        ├── FPR
        └── Processing time

    Step 11.2: Drift Detection (Daily 3 AM)
    ├── Fetch last 7 days data
    ├── Calculate PSI for each feature
    ├── Check thresholds:
    │   ├── PSI > 0.2 → Data drift detected
    │   └── Performance drop > 5% → Model drift detected
    └── If drift detected:
        ├── Log to DriftDetectionLogs
        ├── Send alert
        └── Trigger retraining

    Step 11.3: Auto Rollback (If Needed)
    ├── Monitor: Real-time F1 score
    ├── Threshold: Drop > 5% from baseline
    ├── IF F1 drops from 0.90 to 0.85:
    │   ├── Alert: Critical performance drop
    │   ├── Action: Auto rollback to v1.0.0
    │   └── Notify: Admin team
    └── Rollback time: < 2 minutes


┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 12: NEXT CYCLE (Following Monday)                                     │
└─────────────────────────────────────────────────────────────────────────────┘

    ⏰ Next Monday, 2:00 AM
    ├── Current production: v1.1.0
    ├── Fetch new data from APITransactionLogs
    ├── Train new model: v1.2.0
    ├── Compare with v1.1.0
    └── Repeat cycle...


╔═══════════════════════════════════════════════════════════════════════════════╗
║                           COMPLETE FLOW SUMMARY                                ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Timeline:
├── Week 0: v1.0.0 in production
├── Week 1 Monday 2 AM: Training triggered
├── Week 1 Monday 2:30 AM: v1.1.0 trained, A/B test started
├── Week 2 Monday 2:30 AM: A/B test ends, v1.1.0 promoted
└── Week 3 Monday 2 AM: Next training cycle begins

Key Benefits:
✅ Automated weekly retraining
✅ Safe A/B testing before deployment
✅ Zero downtime deployments
✅ Automatic rollback capability
✅ Continuous performance monitoring
✅ Data drift detection
✅ Complete audit trail

Success Metrics:
├── Training success rate: 95%+
├── A/B test completion rate: 95%+
├── Deployment time: < 5 minutes
├── Rollback time: < 2 minutes
└── Model improvement: 2%+ per cycle
```

---

### 4.2 Alternative Flows

#### 4.2.1 Drift-Triggered Retraining

```
Daily 3:00 AM (Drift Detection)
    ↓
1. Fetch Recent Data (Last 7 days from APITransactionLogs)
    ↓
2. Calculate PSI for each feature
    ↓
3. IF PSI > 0.2 for any feature:
    ├── Log drift detection
    ├── Send alert
    └── Trigger immediate retraining
    ↓
4. Follow same flow as scheduled retraining
```

#### 4.2.2 Manual Rollback Flow

```
Admin Detects Issue → API Call: POST /mlops/versions/v1.0.0/rollback
    ↓
1. Validate v1.0.0 exists
    ↓
2. Update symlink: current → v1.0.0
    ↓
3. Update database: v1.0.0 IsActive=1, v1.1.0 IsActive=0
    ↓
4. Reload models (graceful)
    ↓
5. Verify & notify
    ↓
Rollback complete in < 2 minutes
```

#### 4.2.3 Emergency Stop Flow

```
Critical Bug Detected
    ↓
1. Stop A/B test immediately
    ↓
2. Route 100% traffic to champion
    ↓
3. Mark challenger as failed
    ↓
4. Send emergency alert
    ↓
5. Manual investigation required
```

---

## 📊 5. API Endpoints

### 5.1 MLOps Management Endpoints
**File:** `api/mlops_api.py`


```python
# Training Management
POST   /mlops/train/trigger              # Manual training trigger
GET    /mlops/train/status/{training_id} # Check training status
GET    /mlops/train/history              # Get training history

# Model Versioning
GET    /mlops/versions                   # List all versions
GET    /mlops/versions/{version_id}      # Get version details
GET    /mlops/versions/active            # Get active version
POST   /mlops/versions/{version_id}/activate   # Activate version
POST   /mlops/versions/{version_id}/rollback   # Rollback to version

# A/B Testing
POST   /mlops/ab-test/start              # Start A/B test
GET    /mlops/ab-test/{test_id}          # Get test status
POST   /mlops/ab-test/{test_id}/end      # End test early
GET    /mlops/ab-test/active             # Get active tests

# Monitoring
GET    /mlops/metrics/current            # Current model metrics
GET    /mlops/metrics/compare            # Compare versions
GET    /mlops/drift/status               # Drift detection status
GET    /mlops/performance/logs           # Performance logs

# Configuration
GET    /mlops/config                     # Get MLOps config
PUT    /mlops/config                     # Update config
```

---

## 🛠️ 6. Technology Stack

### 6.1 Core Technologies
- **Python 3.9+**
- **FastAPI** - API framework
- **APScheduler** - Job scheduling
- **Pandas/NumPy** - Data processing
- **Scikit-learn** - Isolation Forest
- **TensorFlow/Keras** - Autoencoder
- **SQL Server** - Database

### 6.2 Optional Enhancements
- **MLflow** - Advanced experiment tracking
- **DVC** - Data version control
- **Prometheus + Grafana** - Advanced monitoring
- **Airflow** - Complex workflow orchestration
- **Redis** - Caching for A/B test routing

---

## 📈 7. Metrics & Monitoring

### 7.1 Model Performance Metrics
```python
{
    "precision": 0.92,
    "recall": 0.88,
    "f1_score": 0.90,
    "false_positive_rate": 0.05,
    "accuracy": 0.94,
    "auc_roc": 0.96
}
```

### 7.2 Training Metrics
```python
{
    "training_duration": 450,        # seconds
    "data_fetch_time": 30,
    "feature_engineering_time": 60,
    "model_training_time": 360,
    "total_records": 50500,
    "historical_records": 50000,
    "recent_records": 500
}
```

### 7.3 Drift Metrics
```python
{
    "psi_scores": {
        "transaction_amount": 0.15,
        "user_avg_amount": 0.08,
        "time_since_last_txn": 0.25  # Drift detected!
    },
    "performance_drop": 0.03,        # 3% drop
    "drift_detected": true
}
```

---

## 🚀 8. Implementation Phases

### Phase 1: Foundation (Week 1-2)

- ✅ Create database tables (ModelVersions, TrainingHistory, etc.)
- ✅ Setup directory structure (mlops/)
- ✅ Implement data_preparation.py
- ✅ Implement model_trainer.py
- ✅ Implement train_pipeline.py
- ✅ Test manual training trigger

### Phase 2: Versioning & Registry (Week 3)
- ✅ Implement model_registry.py
- ✅ Implement rollback_manager.py
- ✅ Create version management API endpoints
- ✅ Test version activation/deactivation
- ✅ Test rollback functionality

### Phase 3: Scheduling (Week 4)
- ✅ Implement cron_scheduler.py
- ✅ Setup weekly/monthly jobs
- ✅ Test scheduled training
- ✅ Implement trigger_manager.py
- ✅ Add manual trigger API

### Phase 4: A/B Testing (Week 5-6)
- ✅ Implement ab_testing.py
- ✅ Implement traffic routing logic
- ✅ Create A/B test API endpoints
- ✅ Implement metrics_calculator.py
- ✅ Test full A/B test cycle

### Phase 5: Monitoring & Drift Detection (Week 7)
- ✅ Implement drift_detector.py
- ✅ Implement performance_tracker.py
- ✅ Setup drift detection cron job
- ✅ Create monitoring API endpoints
- ✅ Test drift-triggered retraining

### Phase 6: Testing & Optimization (Week 8)
- ✅ End-to-end testing
- ✅ Performance optimization
- ✅ Documentation
- ✅ Deployment preparation

---

## 🔐 9. Security & Best Practices

### 9.1 Security Considerations
- API authentication for MLOps endpoints
- Role-based access control (RBAC)
- Audit logging for all operations
- Secure model artifact storage
- Database connection encryption

### 9.2 Best Practices
- Always validate data before training
- Keep training data snapshots
- Log all operations with timestamps
- Implement graceful error handling
- Send notifications for critical events
- Maintain rollback capability
- Test models before deployment
- Monitor performance continuously

---

## 📝 10. Configuration File

**File:** `mlops/config.yaml`

```yaml
training:
  schedule:
    weekly:
      enabled: true
      day: monday
      hour: 2
      minute: 0
    monthly:
      enabled: true
      day: 1
      hour: 2
      minute: 0
  
  data_sources:
    historical_table: TransactionHistoryLogs
    recent_table: APITransactionLogs
    min_recent_records: 100
  
  validation_split: 0.2
  random_seed: 42

versioning:
  storage_path: backend/model_versions
  keep_last_n_versions: 10
  auto_cleanup: true

ab_testing:
  default_duration_days: 7
  default_split: "80/20"
  min_transactions: 1000
  significance_level: 0.05

drift_detection:
  enabled: true
  schedule:
    hour: 3
    minute: 0
  psi_threshold: 0.2
  performance_drop_threshold: 0.05
  auto_retrain: true

monitoring:
  log_predictions: true
  performance_window_days: 7

notifications:
  email:
    enabled: false
    recipients: []
  slack:
    enabled: false
    webhook_url: ""
```

---

## 📊 11. Success Metrics

### 11.1 System Performance
- Training pipeline success rate > 95%
- Average training time < 10 minutes
- Zero-downtime deployments
- Rollback time < 2 minutes

### 11.2 Model Performance
- F1 score improvement > 2% per retraining
- False positive rate < 5%
- Drift detection accuracy > 90%
- A/B test completion rate > 95%

### 11.3 Operational Metrics
- Automated retraining success rate > 90%
- Manual intervention required < 5% of time
- Model version tracking 100% accurate
- Performance monitoring uptime > 99%

---

## 🎯 12. Next Steps

1. **Review & Approve Plan**
   - Stakeholder review
   - Technical feasibility check
   - Resource allocation

2. **Setup Development Environment**
   - Create mlops/ directory structure
   - Install dependencies (APScheduler, etc.)
   - Setup database tables

3. **Start Phase 1 Implementation**
   - Begin with data_preparation.py
   - Test with sample data
   - Iterate and refine

4. **Continuous Monitoring**
   - Track implementation progress
   - Adjust timeline as needed
   - Document learnings

---

## 📚 13. References & Resources

- **APScheduler Documentation:** https://apscheduler.readthedocs.io/
- **MLflow Documentation:** https://mlflow.org/docs/latest/index.html
- **A/B Testing Best Practices:** Statistical significance testing
- **Drift Detection:** PSI calculation methods
- **Model Versioning:** Semantic versioning guidelines

---

## ✅ 14. Checklist

### Pre-Implementation
- [ ] Database tables created
- [ ] Directory structure setup
- [ ] Dependencies installed
- [ ] Configuration file created

### Implementation
- [ ] Data preparation module
- [ ] Model trainer module
- [ ] Training pipeline
- [ ] Model registry
- [ ] Rollback manager
- [ ] A/B testing framework
- [ ] Drift detector
- [ ] Scheduler setup
- [ ] API endpoints
- [ ] Monitoring dashboard

### Testing
- [ ] Unit tests
- [ ] Integration tests
- [ ] End-to-end tests
- [ ] Performance tests
- [ ] Rollback tests

### Deployment
- [ ] Production deployment
- [ ] Monitoring setup
- [ ] Documentation complete
- [ ] Team training

---

**Document Version:** 1.0  
**Last Updated:** February 4, 2026  
**Author:** MLOps Team  
**Status:** Ready for Implementation
