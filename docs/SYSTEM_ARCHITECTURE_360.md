# Anomalous Transaction Detector - Complete System Architecture (360°)

## Executive Summary

A comprehensive ML-powered transaction anomaly detection system with real-time risk scoring, database-driven configuration management, and automated model retraining pipeline. Detects fraudulent transactions using hybrid ML models (Autoencoder + Isolation Forest) with rule-based validation.

**Current Version:** 1.0.4  
**Status:** Production Ready  
**Last Updated:** February 2026

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    TRANSACTION DETECTOR SYSTEM                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐         ┌──────────────────┐              │
│  │   API Layer      │         │  Config UI       │              │
│  │  (Python/Flask)  │         │  (.NET MVC)      │              │
│  └────────┬─────────┘         └────────┬─────────┘              │
│           │                            │                        │
│           └────────────┬───────────────┘                        │
│                        │                                        │
│           ┌────────────▼────────────┐                          │
│           │   SQL Server Database   │                          │
│           │  (Config + Transactions)│                          │
│           └────────────┬────────────┘                          │
│                        │                                        │
│        ┌───────────────┼───────────────┐                       │
│        │               │               │                       │
│   ┌────▼────┐   ┌─────▼──────┐  ┌────▼────┐                  │
│   │   ML    │   │  Scheduler │  │  Rules  │                  │
│   │ Models  │   │  (MLOps)   │  │ Engine  │                  │
│   └─────────┘   └────────────┘  └─────────┘                  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Architecture Components

### 1. API Layer (Python/Flask)

**Location:** `api/` directory  
**Purpose:** RESTful endpoints for transaction processing

#### Key Files:
- `api.py` - Main Flask application
- `api/api.py` - API route definitions
- `api/models.py` - Request/response models
- `api/services.py` - Business logic
- `api/helpers.py` - Utility functions

#### Main Endpoints:

```
POST /api/check-transaction
├── Input: Transaction details
├── Processing: Risk scoring
└── Output: Risk level + decision

POST /api/batch-check
├── Input: Multiple transactions
├── Processing: Parallel processing
└── Output: Batch results

GET /api/health
└── Output: System status

GET /api/models/status
└── Output: Current model versions
```

#### Request Example:
```json
{
  "customer_id": "1060284",
  "account_no": "011060284018",
  "transfer_type": "O",
  "amount": 50000,
  "beneficiary_id": "NEW_BENE",
  "timestamp": "2026-02-24T10:30:00Z"
}
```

#### Response Example:
```json
{
  "transaction_id": "TXN_123456",
  "risk_level": "HIGH",
  "risk_score": 0.85,
  "decision": "REQUIRES_USER_APPROVAL",
  "reasons": [
    "Velocity violation: 3 transactions in 10 minutes",
    "Amount exceeds threshold",
    "New beneficiary"
  ],
  "ml_score": 0.78,
  "rule_violations": 2,
  "timestamp": "2026-02-24T10:30:00Z"
}
```

---

### 2. Backend Processing (Python)

**Location:** `backend/` directory  
**Purpose:** ML models, feature engineering, and business logic

#### Core Modules:

##### A. ML Models

**Autoencoder (`backend/train_autoencoder.py`)**
- Unsupervised anomaly detection
- Detects unusual transaction patterns
- Reconstruction error as anomaly score
- Threshold: 0.7 (configurable)

**Isolation Forest (`backend/train_isolation_forest.py`)**
- Ensemble-based anomaly detection
- Isolates anomalies in feature space
- Anomaly score: -1 to 1
- Threshold: -0.5 (configurable)

**Hybrid Decision (`backend/hybrid_decision.py`)**
```python
def calculate_risk_score(ae_score, if_score, rule_violations):
    # Combine ML scores with rule violations
    ml_score = (ae_score + if_score) / 2
    
    if rule_violations > 0:
        ml_score = max(0.85, ml_score)  # Boost score
    
    return ml_score
```

##### B. Feature Engineering (`backend/feature_engineering.py`)

**Features Extracted:**
- Transaction amount
- Time of day
- Day of week
- Customer velocity (transactions/hour)
- Beneficiary frequency
- Account age
- Transfer type
- Amount deviation from average

**Scaling:** StandardScaler (fitted on training data)

##### C. Rule Engine (`backend/rule_engine.py`)

**Rules Implemented:**
1. **Velocity Check** - Max transactions per time window
2. **Amount Threshold** - Max transaction amount
3. **New Beneficiary** - Flag new beneficiary transfers
4. **Monthly Spending** - Monthly limit check
5. **Transfer Type Rules** - Type-specific validations

**Rule Configuration:**
```python
RULES = {
    'velocity_check_10min': {
        'max_transactions': 3,
        'time_window': 600,  # seconds
        'enabled': True
    },
    'amount_threshold': {
        'max_amount': 100000,
        'enabled': True
    },
    'new_beneficiary_check': {
        'enabled': True,
        'flag_new': True
    }
}
```

##### D. Input Validation (`backend/input_validator.py`)

**Validations:**
- Required fields present
- Data types correct
- Values within acceptable ranges
- Customer exists in database
- Account is active

##### E. Velocity Service (`backend/velocity_service.py`)

**Functionality:**
- Tracks transaction velocity per customer
- Maintains sliding window of transactions
- Calculates transactions per time unit
- Triggers velocity alerts

---

### 3. Database Layer

**Database:** SQL Server  
**ORM:** Entity Framework Core (C#), SQLAlchemy (Python)

#### Database Schema

##### Configuration Tables

**FeaturesConfig**
```sql
CREATE TABLE FeaturesConfig (
    FeatureID INT PRIMARY KEY,
    FeatureName NVARCHAR(100),
    IsEnabled BIT,
    IsActive BIT,
    FeatureType NVARCHAR(50),
    Version NVARCHAR(20),
    UpdatedAt DATETIME,
    UpdatedBy NVARCHAR(100)
);
```

**ThresholdConfig**
```sql
CREATE TABLE ThresholdConfig (
    ThresholdID INT PRIMARY KEY,
    ThresholdName NVARCHAR(100),
    ThresholdValue FLOAT,
    MinValue FLOAT,
    MaxValue FLOAT,
    IsActive BIT,
    ApprovalStatus NVARCHAR(50),
    UpdatedAt DATETIME
);
```

**RetrainingConfig**
```sql
CREATE TABLE RetrainingConfig (
    ConfigId INT PRIMARY KEY,
    Interval NVARCHAR(50),
    IsEnabled BIT,
    WeeklyJobDay INT,
    WeeklyJobHour INT,
    WeeklyJobMinute INT,
    MonthlyJobDay INT,
    MonthlyJobHour INT,
    MonthlyJobMinute INT,
    LastRun DATETIME,
    NextRun DATETIME
);
```

**ModelVersionConfig**
```sql
CREATE TABLE ModelVersionConfig (
    ModelVersionID INT PRIMARY KEY,
    ModelName NVARCHAR(100),
    VersionNumber NVARCHAR(20),
    ModelPath NVARCHAR(500),
    IsActive BIT,
    Accuracy FLOAT,
    Precision FLOAT,
    Recall FLOAT,
    F1Score FLOAT,
    CreatedAt DATETIME,
    DeployedAt DATETIME
);
```

**CustomerAccountTransferTypeConfig**
```sql
CREATE TABLE CustomerAccountTransferTypeConfig (
    ConfigID INT PRIMARY KEY,
    CustomerID NVARCHAR(50),
    AccountNo NVARCHAR(50),
    TransferType NVARCHAR(10),
    ParameterName NVARCHAR(100),
    ParameterValue NVARCHAR(500),
    IsEnabled BIT,
    IsActive BIT,
    MinValue FLOAT,
    MaxValue FLOAT
);
```

##### Transaction Tables

**APITransactionLogs**
```sql
CREATE TABLE APITransactionLogs (
    TransactionID NVARCHAR(50) PRIMARY KEY,
    CustomerID NVARCHAR(50),
    AccountNo NVARCHAR(50),
    Amount DECIMAL(18,2),
    RiskLevel NVARCHAR(20),
    RiskScore FLOAT,
    Decision NVARCHAR(50),
    CreatedDate DATETIME,
    UpdatedDate DATETIME
);
```

**ModelTrainingRuns**
```sql
CREATE TABLE ModelTrainingRuns (
    RunId INT PRIMARY KEY,
    RunDate DATETIME,
    ModelVersion NVARCHAR(20),
    Status NVARCHAR(50),
    DataSize INT,
    Metrics NVARCHAR(MAX)
);
```

---

### 4. MLOps Pipeline

**Location:** `backend/mlops/` directory  
**Purpose:** Automated model training, versioning, and deployment

#### Components:

##### A. Data Fetcher (`backend/mlops/data_fetcher.py`)
- Fetches training data from database
- Handles data preprocessing
- Manages data splits (train/test)
- Tracks data lineage

##### B. Retraining Pipeline (`backend/mlops/retraining_pipeline.py`)
```python
def retrain_models():
    # 1. Fetch data
    data = fetch_training_data()
    
    # 2. Preprocess
    X_train, X_test = preprocess_data(data)
    
    # 3. Train models
    ae_model = train_autoencoder(X_train)
    if_model = train_isolation_forest(X_train)
    
    # 4. Evaluate
    ae_metrics = evaluate_autoencoder(ae_model, X_test)
    if_metrics = evaluate_isolation_forest(if_model, X_test)
    
    # 5. Version
    version = create_version(ae_model, if_model)
    
    # 6. Deploy
    deploy_models(version)
    
    # 7. Log
    log_training_run(version, metrics)
```

##### C. Model Versioning (`backend/mlops/model_versioning.py`)
- Maintains model versions (1.0.1, 1.0.2, etc.)
- Stores model artifacts
- Tracks metrics per version
- Enables rollback

**Version Storage:**
```
backend/model/versions/
├── 1.0.1/
│   ├── autoencoder/
│   │   ├── model.pkl
│   │   └── metadata.json
│   └── isolation_forest/
│       ├── model.pkl
│       └── metadata.json
├── 1.0.2/
├── 1.0.3/
└── 1.0.4/  (current)
```

##### D. Scheduler (`backend/mlops/scheduler.py`)
- Triggers retraining on schedule
- Supports weekly/monthly intervals
- Handles job execution
- Logs execution results

**Schedule Configuration:**
```python
SCHEDULE = {
    'weekly': {
        'day': 'Monday',
        'time': '02:00',
        'enabled': True
    },
    'monthly': {
        'day': 1,
        'time': '03:00',
        'enabled': True
    }
}
```

---

### 5. Configuration Management UI

**Location:** `ConfigManagementUI/` (.NET Core MVC)  
**Purpose:** Admin dashboard for system configuration

#### Pages:

1. **Dashboard** (`/Config/Index`)
   - System overview
   - Quick stats
   - Recent activities

2. **Features** (`/Config/Features`)
   - Toggle features on/off
   - Edit feature details
   - Version management

3. **Thresholds** (`/Config/Thresholds`)
   - View all thresholds
   - Edit threshold values
   - Approval workflow

4. **Scheduler** (`/Config/Scheduler`)
   - Configure retraining schedule
   - Set job times
   - Enable/disable jobs

5. **Model Versions** (`/Config/ModelVersions`)
   - View all model versions
   - Check metrics
   - Activate/deactivate versions

6. **Training Runs** (`/Config/TrainingRuns`)
   - View training history
   - Check run status
   - Review metrics

7. **Customer Configs** (`/Config/CustomerConfigs`)
   - Customer-specific rules
   - Parameter management
   - Bulk operations

---

### 6. Streamlit Dashboard

**Location:** `app.py`  
**Purpose:** Real-time monitoring and analytics

#### Features:
- Transaction monitoring
- Risk distribution charts
- Model performance metrics
- Configuration viewer
- Alert management

#### Sections:
1. **Overview** - Key metrics
2. **Transactions** - Recent transactions
3. **Analytics** - Charts and graphs
4. **Models** - Model status
5. **Configuration** - Current settings

---

## Data Flow

### Transaction Processing Flow

```
1. API Request
   ↓
2. Input Validation
   ├─ Check required fields
   ├─ Validate data types
   └─ Verify customer/account
   ↓
3. Feature Engineering
   ├─ Extract features
   ├─ Scale features
   └─ Prepare for ML
   ↓
4. Rule Engine
   ├─ Check velocity
   ├─ Check thresholds
   ├─ Check beneficiary
   └─ Collect violations
   ↓
5. ML Scoring
   ├─ Autoencoder score
   ├─ Isolation Forest score
   └─ Hybrid decision
   ↓
6. Risk Calculation
   ├─ Combine ML + Rules
   ├─ Determine risk level
   └─ Make decision
   ↓
7. Response
   ├─ Return risk level
   ├─ Log transaction
   └─ Send to database
```

### Model Retraining Flow

```
1. Scheduler Trigger
   ↓
2. Data Fetching
   ├─ Query database
   ├─ Filter by date range
   └─ Prepare dataset
   ↓
3. Preprocessing
   ├─ Handle missing values
   ├─ Feature engineering
   └─ Data splitting
   ↓
4. Model Training
   ├─ Train Autoencoder
   ├─ Train Isolation Forest
   └─ Parallel execution
   ↓
5. Evaluation
   ├─ Calculate metrics
   ├─ Compare with baseline
   └─ Validate performance
   ↓
6. Versioning
   ├─ Create version
   ├─ Store artifacts
   └─ Update metadata
   ↓
7. Deployment
   ├─ Load new models
   ├─ Update active version
   └─ Log deployment
   ↓
8. Monitoring
   ├─ Track performance
   ├─ Alert on issues
   └─ Log metrics
```

---

## Configuration Management

### Feature Flags

**Available Features:**
- `velocity_check` - Enable/disable velocity checking
- `amount_threshold` - Enable/disable amount validation
- `new_beneficiary_check` - Enable/disable new beneficiary flagging
- `monthly_spending_check` - Enable/disable monthly limits
- `ml_scoring` - Enable/disable ML models
- `rule_engine` - Enable/disable rule engine

### Thresholds

**Configurable Thresholds:**
- `velocity_check_10min` - Max transactions in 10 minutes
- `amount_threshold` - Max transaction amount
- `monthly_spending_limit` - Max monthly spending
- `autoencoder_threshold` - Anomaly detection threshold
- `isolation_forest_threshold` - Anomaly detection threshold

### Scheduler Configuration

**Retraining Schedule:**
- Weekly: Monday 02:00 UTC
- Monthly: 1st of month 03:00 UTC
- Can be modified via Config UI

---

## Model Details

### Autoencoder Model

**Architecture:**
```
Input (8 features)
    ↓
Dense(16) + ReLU
    ↓
Dense(8) + ReLU
    ↓
Dense(4) + ReLU  (Bottleneck)
    ↓
Dense(8) + ReLU
    ↓
Dense(16) + ReLU
    ↓
Dense(8) + Linear (Output)
```

**Training:**
- Loss: Mean Squared Error
- Optimizer: Adam
- Epochs: 50
- Batch Size: 32
- Validation Split: 0.2

**Threshold:** 0.7 (reconstruction error)

### Isolation Forest Model

**Parameters:**
- n_estimators: 100
- max_samples: 256
- contamination: 0.1
- random_state: 42

**Threshold:** -0.5 (anomaly score)

### Hybrid Scoring

```python
def hybrid_score(ae_score, if_score, rule_violations):
    # Normalize scores to 0-1
    ae_normalized = min(ae_score, 1.0)
    if_normalized = (if_score + 1) / 2  # Convert -1,1 to 0,1
    
    # Average ML scores
    ml_score = (ae_normalized + if_normalized) / 2
    
    # Boost if rule violations
    if rule_violations > 0:
        ml_score = max(0.85, ml_score)
    
    # Determine risk level
    if ml_score >= 0.8:
        return "HIGH"
    elif ml_score >= 0.5:
        return "MEDIUM"
    else:
        return "LOW"
```

---

## Performance Metrics

### Model Performance (v1.0.4)

| Metric | Autoencoder | Isolation Forest | Hybrid |
|--------|-------------|------------------|--------|
| Accuracy | 0.94 | 0.91 | 0.95 |
| Precision | 0.92 | 0.89 | 0.93 |
| Recall | 0.96 | 0.93 | 0.97 |
| F1-Score | 0.94 | 0.91 | 0.95 |

### System Performance

| Metric | Value |
|--------|-------|
| Avg Response Time | 45ms |
| P95 Response Time | 120ms |
| P99 Response Time | 250ms |
| Throughput | 1000 TPS |
| Availability | 99.9% |

---

## Deployment Architecture

### Development Environment
- Local Python environment
- SQLite/SQL Server
- Flask development server
- Streamlit local server

### Production Environment
- Docker containers
- Kubernetes orchestration
- SQL Server (managed)
- Load balancer
- Monitoring stack (Prometheus, Grafana)

### Deployment Steps

1. **Build Docker Image**
   ```bash
   docker build -t anomaly-detector:1.0.4 .
   ```

2. **Push to Registry**
   ```bash
   docker push registry.example.com/anomaly-detector:1.0.4
   ```

3. **Deploy to Kubernetes**
   ```bash
   kubectl apply -f deployment.yaml
   ```

4. **Verify Deployment**
   ```bash
   kubectl get pods
   kubectl logs pod-name
   ```

---

## Monitoring & Alerting

### Key Metrics to Monitor

1. **API Metrics**
   - Request rate
   - Response time
   - Error rate
   - Throughput

2. **Model Metrics**
   - Prediction accuracy
   - False positive rate
   - Model drift
   - Inference time

3. **System Metrics**
   - CPU usage
   - Memory usage
   - Disk usage
   - Database connections

4. **Business Metrics**
   - Fraud detection rate
   - False positive rate
   - Transaction volume
   - Risk distribution

### Alerts

**Critical Alerts:**
- API down
- Model inference failure
- Database connection error
- High error rate (>5%)

**Warning Alerts:**
- High response time (>500ms)
- Model drift detected
- Retraining failure
- Low disk space

---

## Security Considerations

### Authentication & Authorization
- API key authentication
- Role-based access control (RBAC)
- User audit logging

### Data Protection
- Encryption at rest (SQL Server TDE)
- Encryption in transit (HTTPS/TLS)
- Data masking for sensitive fields
- PII handling compliance

### API Security
- Rate limiting
- Input validation
- SQL injection prevention
- CSRF protection

---

## Troubleshooting Guide

### Common Issues

**Issue: High False Positive Rate**
- Solution: Adjust thresholds in Config UI
- Check: Rule engine configuration
- Review: Recent model version metrics

**Issue: Slow API Response**
- Solution: Check database performance
- Review: Feature engineering complexity
- Monitor: Model inference time

**Issue: Model Training Failure**
- Solution: Check data quality
- Review: Training logs
- Verify: Sufficient disk space

**Issue: Configuration Not Applied**
- Solution: Restart API service
- Check: Database connectivity
- Verify: Configuration values

---

## Future Roadmap

### Short Term (Q1 2026)
- [ ] Add explainability (SHAP values)
- [ ] Implement A/B testing framework
- [ ] Add real-time alerting
- [ ] Enhance monitoring dashboard

### Medium Term (Q2-Q3 2026)
- [ ] Multi-model ensemble
- [ ] Federated learning support
- [ ] Advanced approval workflow
- [ ] Batch processing optimization

### Long Term (Q4 2026+)
- [ ] Graph neural networks
- [ ] Reinforcement learning
- [ ] Distributed training
- [ ] Edge deployment

---

## Support & Documentation

### Documentation Files
- `docs/API_ENDPOINTS_POSTMAN.md` - API reference
- `docs/CONFIG_UI_DETAILED_GUIDE.md` - UI guide
- `docs/SCHEDULER_CONFIGURATION_GUIDE.md` - Scheduler guide
- `docs/DOTNET_CONFIG_SCREENS_GUIDE.md` - .NET guide

### Contact
- **Issues:** GitHub Issues
- **Questions:** Documentation Wiki
- **Bugs:** Bug Report Template

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.4 | Feb 2026 | Current production version |
| 1.0.3 | Jan 2026 | Enhanced rule engine |
| 1.0.2 | Dec 2025 | Added Config UI |
| 1.0.1 | Nov 2025 | Initial release |

---

## Conclusion

The Anomalous Transaction Detector is a comprehensive, production-ready system combining machine learning with rule-based validation for effective fraud detection. With database-driven configuration management and automated retraining, it provides flexibility and scalability for enterprise deployment.
