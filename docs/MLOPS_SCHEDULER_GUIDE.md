MLOps Scheduler - Complete Guide

Overview

MLOps scheduler automatically retrains fraud detection models on a configurable schedule. Models adapt to new fraud patterns and user behavior changes without manual intervention.

Architecture

backend/mlops/
├── data_fetcher.py - Fetch training data from database
├── model_versioning.py - Version management and storage
├── retraining_pipeline.py - Orchestrate full retraining process
├── scheduler.py - APScheduler setup and config management
└── __init__.py - Package initialization

Core Components

1. Data Fetcher (data_fetcher.py)

Fetches training data from two sources:
- TransactionHistoryLogs: Historical baseline data (all records)
- APITransactionLogs: Recent labeled data (last 30 days by default)

Process:
1. Fetch historical data from TransactionHistoryLogs
2. Fetch recent data from APITransactionLogs (CreatedAt >= since_date)
3. Merge datasets and remove duplicates
4. Return combined training data

Key Methods:
- fetch_historical_data(): Get all historical transactions
- fetch_recent_data(since_date): Get recent transactions
- merge_datasets(historical, recent): Combine and deduplicate
- fetch_training_data(since_date): Main entry point

2. Model Versioning (model_versioning.py)

Manages model versions and metadata storage.

Directory Structure:
backend/model/
├── versions/
│   ├── 1.0.0/
│   │   ├── isolation_forest/
│   │   │   ├── model.pkl
│   │   │   ├── scaler.pkl
│   │   │   └── metadata.json
│   │   └── autoencoder/
│   │       ├── model.pkl
│   │       ├── scaler.pkl
│   │       └── metadata.json
│   └── 1.0.1/
│       └── ...
└── current_version.txt

Key Methods:
- get_next_version(): Auto-increment version (1.0.0 → 1.0.1)
- get_current_version(): Get active version
- save_model_version(model, scaler, version, model_type, metrics): Save versioned model
- set_current_version(version): Update active version
- load_model_version(version, model_type): Load specific version
- list_versions(): List all available versions

3. Retraining Pipeline (retraining_pipeline.py)

Orchestrates complete model retraining process.

8-Step Process:

Step 1: Fetch Data
- Query TransactionHistoryLogs and APITransactionLogs
- Combine datasets
- Result: 3000+ training records

Step 2: Engineer Features
- Call engineer_features(df) function with fetched data
- Accepts dataframe parameter for live data processing
- Respects enabled features from FeaturesConfig table
- Result: 43 features per transaction
- Note: Function now uses live database data instead of static CSV

Step 3: Train Isolation Forest
- Load engineered data
- Train anomaly detection model
- Metrics: n_samples, anomaly_count, anomaly_rate

Step 4: Train Autoencoder
- Load engineered data
- Train deep learning model
- Metrics: threshold, mean_error, std

Step 5: Validate Models
- Check if metrics exist
- Verify model quality
- Ensure accuracy thresholds met

Step 6: Save Versioned Models
- Save both models with metadata
- Create version directory structure
- Store training metrics

Step 7: Update Current Version
- Write new version to current_version.txt
- API loads new models on next request

Step 8: Log Training Run
- Insert record into ModelTrainingRuns table
- Track success/failure
- Store metrics for analysis

Key Methods:
- fetch_data(since_date): Step 1
- engineer_features_step(df): Step 2 - Passes dataframe to engineer_features()
- train_isolation_forest(df): Step 3
- train_autoencoder(df): Step 4
- validate_models(if_metrics, ae_metrics): Step 5
- save_models(version, if_metrics, ae_metrics): Step 6
- update_version(version): Step 7
- log_training_run(version, status, metrics): Step 8
- run(since_date): Execute full pipeline

Data Flow in Pipeline:
1. Fetch data from database (TransactionHistoryLogs + APITransactionLogs)
2. Pass fetched dataframe to engineer_features_step()
3. engineer_features_step() calls engineer_features(df) with live data
4. Features are engineered on fresh database data (not static CSV)
5. Engineered features saved to data/feature_datasetv2.csv
6. Models trained on fresh engineered features

4. Scheduler (scheduler.py)

Manages job scheduling and dynamic interval configuration.

Fixed Issues:
- scheduler.scheduler.add_job() now correctly accesses APScheduler's BackgroundScheduler
- Config checker job properly initialized with interval trigger
- Weekly and monthly jobs scheduled correctly

Supported Intervals:
- 1H: Every 1 hour
- 1D: Every 1 day
- 1W: Every 1 week (default)
- 1M: Every 30 days
- 1Y: Every 365 days

Key Methods:
- add_weekly_job(day_of_week, hour, minute): Fixed weekly schedule
- add_monthly_job(day, hour, minute): Fixed monthly schedule
- add_interval_job(interval): Dynamic interval (1H, 1D, 1W, 1M, 1Y)
- check_and_update_schedule(): Monitor config table for changes (runs every 5 min)
- start(): Start scheduler
- stop(): Stop scheduler

Configuration

RetrainingConfig Table

CREATE TABLE RetrainingConfig (
    ConfigId INT PRIMARY KEY IDENTITY(1,1),
    Interval VARCHAR(10) DEFAULT '1W',
    IsEnabled BIT DEFAULT 1,
    LastRun DATETIME,
    NextRun DATETIME,
    CreatedAt DATETIME DEFAULT GETDATE(),
    UpdatedAt DATETIME DEFAULT GETDATE()
)

INSERT INTO RetrainingConfig (Interval, IsEnabled) VALUES ('1W', 1)

Configuration Options:
- Interval: '1H', '1D', '1W', '1M', '1Y'
- IsEnabled: 1 (enabled) or 0 (disabled)
- LastRun: Timestamp of last training
- NextRun: Estimated next training time

Dynamic Configuration

1. Update config table directly (no API needed)
2. Scheduler checks every 5 minutes
3. Detects interval change
4. Updates job automatically
5. New interval takes effect immediately

Example:
UPDATE RetrainingConfig SET Interval = '1D' WHERE ConfigId = 1

Scheduler will detect change within 5 minutes and switch to daily retraining.

API Integration

Startup Event (api/api.py)

@app.on_event("startup")
async def startup_event():
    start_scheduler()
    logger.info("MLOps Scheduler started")

Shutdown Event

@app.on_event("shutdown")
async def shutdown_event():
    stop_scheduler()
    logger.info("MLOps Scheduler stopped")

Manual Trigger Endpoint

POST /api/mlops/trigger-retraining
Authorization: Basic auth required
Response: {"status": "success" or "failed"}

Monitoring

ModelTrainingRuns Table

CREATE TABLE ModelTrainingRuns (
    RunId INT PRIMARY KEY IDENTITY,
    RunDate DATETIME DEFAULT GETDATE(),
    ModelVersion VARCHAR(20),
    Status VARCHAR(20),
    DataSize INT,
    Metrics NVARCHAR(MAX)
)

Track all training runs:
- RunDate: When training executed
- ModelVersion: Version trained (1.0.1, 1.0.2, etc.)
- Status: SUCCESS or FAILED
- Metrics: JSON with training metrics

Error Handling

Graceful Degradation:
- If data fetch fails: Log error, skip training
- If model training fails: Keep previous version
- If database unavailable: Use default config
- If versioning fails: Log error, continue

Logging:
- All operations logged with timestamps
- Errors logged with full stack trace
- Metrics logged for analysis

Performance

Data Processing:
- 4000+ records processed per training
- 43 features engineered per record
- ~2-5 minutes per full training cycle

Storage:
- Each version: ~50-100 MB (models + metadata)
- Keep last 10 versions: ~500-1000 MB
- Old versions can be archived

Deployment Checklist

Before Production:
1. Create RetrainingConfig table
2. Insert default configuration
3. Create ModelTrainingRuns table
4. Restart API container
5. Verify scheduler started in logs
6. Test manual trigger endpoint
7. Monitor first training run
8. Verify models saved in versions/

Troubleshooting

Scheduler Not Running:
- Check API startup logs
- Verify APScheduler installed
- Check database connection

Models Not Retraining:
- Check RetrainingConfig table exists
- Verify Interval and IsEnabled values
- Check logs for errors
- Manually trigger: POST /api/mlops/trigger-retraining

Data Not Fetching:
- Verify TransactionHistoryLogs has data
- Verify APITransactionLogs has recent data
- Check database connection
- Verify column names (CreateDate, CreatedAt)

Models Not Saving:
- Check backend/model/versions/ directory exists
- Verify write permissions
- Check disk space
- Check logs for errors

Complete Project Flowchart

┌─────────────────────────────────────────────────────────────────┐
│                    Client Application                            │
│                  (Postman / Frontend)                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Server                                │
│                   (api/api.py)                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Endpoints:                                               │   │
│  │ - POST /api/analyze-transaction (fraud detection)       │   │
│  │ - POST /api/mlops/trigger-retraining (manual trigger)   │   │
│  │ - GET /api/health                                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                         │                                        │
│  ┌──────────────────────┴──────────────────────┐                │
│  │                                             │                │
│  ↓                                             ↓                │
│ Startup Event                          Shutdown Event           │
│ start_scheduler()                      stop_scheduler()         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
        ┌────────────────────────────────┐
        │   APScheduler (Background)     │
        │                                │
        │ Jobs:                          │
        │ 1. Config Checker (5 min)      │
        │ 2. Weekly Job (Monday 2 AM)    │
        │ 3. Monthly Job (1st 3 AM)      │
        │ 4. Interval Job (Dynamic)      │
        └────────────────┬───────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                 │
        ↓                                 ↓
   Config Checker              Retraining Pipeline
   (Every 5 min)               (On Schedule)
        │                                 │
        ↓                                 ↓
   Check RetrainingConfig      STEP 1: Fetch Data
   Table for changes           ├─ TransactionHistoryLogs
        │                      └─ APITransactionLogs
        ↓                                 │
   Interval Changed?                      ↓
   ├─ Yes: Update Job          STEP 2: Engineer Features
   └─ No: Continue             ├─ 43 ML features
                               └─ Respect FeaturesConfig
                                         │
                                         ↓
                               STEP 3: Train Models
                               ├─ Isolation Forest
                               └─ Autoencoder
                                         │
                                         ↓
                               STEP 4: Validate
                               ├─ Check metrics
                               └─ Verify quality
                                         │
                                         ↓
                               STEP 5: Save Versions
                               ├─ v1.0.1/isolation_forest/
                               ├─ v1.0.1/autoencoder/
                               └─ metadata.json
                                         │
                                         ↓
                               STEP 6: Update Version
                               └─ current_version.txt
                                         │
                                         ↓
                               STEP 7: Log Run
                               └─ ModelTrainingRuns table
                                         │
                                         ↓
        ┌────────────────────────────────┘
        │
        ↓
   Next Transaction Request
        │
        ↓
   Load Current Model Version
        │
        ↓
   Analyze Transaction
   ├─ Rule Engine
   ├─ Isolation Forest
   └─ Autoencoder
        │
        ↓
   Return Fraud Decision
        │
        ↓
   Log to APITransactionLogs
        │
        ↓
   Response to Client

Data Flow

Transaction Analysis:
Client → API → Rule Engine + ML Models → Decision → Database

Model Retraining:
Database (TransactionHistoryLogs + APITransactionLogs)
    ↓
Data Fetcher (merge & deduplicate)
    ↓
Feature Engineering (43 features)
    ↓
Model Training (IF + AE)
    ↓
Model Versioning (save v1.0.1)
    ↓
API loads new models
    ↓
Next transaction uses new models

Configuration Flow:

User updates RetrainingConfig table
    ↓
Scheduler checks every 5 minutes
    ↓
Detects interval change
    ↓
Updates job automatically
    ↓
New interval takes effect

Key Features

1. Automated Retraining
   - No manual intervention needed
   - Scheduled or on-demand
   - Configurable intervals

2. Model Versioning
   - Track all model versions
   - Easy rollback to previous versions
   - Metadata stored with each version

3. Dynamic Configuration
   - Change interval from database
   - No API restart needed
   - Takes effect within 5 minutes

4. Comprehensive Logging
   - All training runs tracked
   - Metrics stored for analysis
   - Error handling and recovery

5. Production Ready
   - Graceful error handling
   - Database integration
   - Monitoring and alerting support

Recent Updates (v1.0.1)

1. Feature Engineering Enhancement
   - engineer_features() now accepts dataframe parameter
   - Retraining pipeline passes live database data to feature engineering
   - Eliminates dependency on static CSV files
   - Models now train on fresh, real-time data

2. Scheduler Fix
   - Fixed scheduler.add_job() call to use scheduler.scheduler.add_job()
   - Config checker job now properly initialized
   - All scheduled jobs execute correctly

3. Data Flow Improvement
   - Database → Data Fetcher → Feature Engineering → Model Training
   - feature_datasetv2.csv updated with fresh engineered features
   - Models trained on current transaction patterns

Next Steps

1. Create RetrainingConfig table
2. Create ModelTrainingRuns table
3. Restart API container
4. Monitor scheduler in logs
5. Test manual trigger
6. Verify models retraining
7. Monitor performance metrics
8. Set up alerts for failures
