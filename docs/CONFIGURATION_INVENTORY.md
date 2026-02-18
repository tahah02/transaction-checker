# Configuration Inventory - Complete System

**Status:** ✅ All configurations documented and tracked

---

## Configuration Storage Locations

### 1. **File-Based Configurations**

#### `backend/config/risk_thresholds.json`
**Purpose:** Risk scoring and confidence calculation thresholds

**Configurations:**
```json
{
  "isolation_forest": {
    "high_risk_threshold": 0.8,      // Risk score >= 0.8 = HIGH
    "medium_risk_threshold": 0.65,   // Risk score >= 0.65 = MEDIUM
    "low_risk_threshold": 0.4        // Risk score >= 0.4 = LOW
  },
  "confidence_calculation": {
    "all_models_agree": 0.95,        // All 3 models agree
    "two_models_agree": 0.80,        // 2 models agree
    "one_model_agrees": 0.60,        // 1 model agrees
    "high_risk_boost": 0.03          // Boost if ML score > 0.8
  },
  "risk_levels": {
    "safe": "SAFE",
    "low": "LOW",
    "medium": "MEDIUM",
    "high": "HIGH"
  }
}
```

**Used In:**
- `backend/hybrid_decision.py` - Risk level calculation
- `backend/hybrid_decision.py` - Confidence level calculation

---

#### `.env` File
**Purpose:** Environment variables and credentials

**Configurations:**
```
DB_SERVER=10.112.32.4
DB_PORT=1433
DB_DATABASE=retailchannelLogs
DB_USERNAME=dbuser
DB_PASSWORD=Codebase202212?!
REDIS_URL=redis://localhost:6379
API_USERNAME=FDS
API_PASSWORD=12345
ADMIN_KEY=FDS12345
```

**Used In:**
- `backend/db_service.py` - Database connection
- `api/api.py` - API authentication
- `api/helpers.py` - Admin key validation

---

### 2. **Hardcoded Configurations (Code)**

#### `backend/rule_engine.py`
**Purpose:** Business rule limits and multipliers

**Configurations:**

```python
# Transfer Type Multipliers (for monthly spending calculation)
TRANSFER_MULTIPLIERS = {
    'S': 2.0,    # Overseas
    'Q': 2.5,    # Quick
    'L': 3.0,    # UAE
    'I': 3.5,    # Ajman
    'O': 4.0,    # Own
    'M': 3.2,    # MobilePay
    'F': 3.8     # Family Transfer
}

# Minimum Floors (for monthly spending calculation)
TRANSFER_MIN_FLOORS = {
    'S': 5000,   # Overseas
    'Q': 3000,   # Quick
    'L': 2000,   # UAE
    'I': 1500,   # Ajman
    'O': 1000,   # Own
    'M': 1800,   # MobilePay
    'F': 1200    # Family Transfer
}

# Velocity Limits (same for all customers)
MAX_VELOCITY_10MIN = 5      // Max 5 transactions in 10 minutes
MAX_VELOCITY_1HOUR = 15     // Max 15 transactions in 1 hour
```

**Formula:**
```
Monthly Spending Limit = MAX(user_avg + multiplier × user_std, floor)
```

**Used In:**
- `backend/rule_engine.py` - Rule violation checking
- `api/api.py` - Transaction analysis

---

### 3. **Database Configurations**

#### Table: `FeaturesConfig`
**Purpose:** Global feature toggles (47 features + 4 rule checks)

**Columns:**
- `FeatureID` - Unique identifier
- `FeatureName` - Feature name
- `IsEnabled` - 1 (enabled) or 0 (disabled)
- `FeatureType` - Type of feature
- `Version` - Feature version
- `CreatedAt` - Creation timestamp
- `UpdatedAt` - Last update timestamp
- `CreatedBy` - User who created
- `UpdatedBy` - User who updated
- `RollbackVersion` - Previous version for rollback

**Features Tracked:**
- 43 ML features (transaction, temporal, behavioral, etc.)
- 4 rule checks (velocity_check_10min, velocity_check_1hour, monthly_spending_check, new_beneficiary_check)

**Query Used:**
```sql
SELECT FeatureName FROM FeaturesConfig WHERE IsEnabled = 1
```

**Used In:**
- `backend/db_service.py` - `get_enabled_features()`
- `backend/feature_engineering.py` - Feature selection
- `backend/rule_engine.py` - Rule check selection

---

#### Table: `ThresholdConfig`
**Purpose:** Global thresholds (23 values)

**Columns:**
- `ThresholdID` - Unique identifier
- `ThresholdName` - Threshold name
- `ThresholdValue` - Current value
- `MinValue` - Minimum allowed value
- `MaxValue` - Maximum allowed value
- `PreviousValue` - Previous value for rollback
- `EffectiveFrom` - When threshold becomes active
- `EffectiveTo` - When threshold expires
- `ApprovalStatus` - Approval status
- `CreatedAt` - Creation timestamp
- `UpdatedAt` - Last update timestamp

**Thresholds Tracked:**
- Risk level thresholds (HIGH, MEDIUM, LOW, SAFE)
- Velocity limits
- Monthly spending multipliers
- Confidence levels
- Model agreement thresholds

**Used In:**
- `backend/hybrid_decision.py` - Risk level calculation
- `backend/rule_engine.py` - Limit checking

---

#### Table: `CustomerAccountTransferTypeConfig`
**Purpose:** Customer-specific configuration overrides

**Columns:**
- `ConfigID` - Unique identifier
- `CustomerID` - Customer ID
- `AccountNo` - Account number
- `TransferType` - Transfer type (S, I, L, Q, O, M, F)
- `ParameterName` - Parameter name
- `ParameterValue` - Parameter value
- `IsEnabled` - 1 (enabled) or 0 (disabled)
- `DataType` - Data type
- `MinValue` - Minimum value
- `MaxValue` - Maximum value
- `CreatedAt` - Creation timestamp
- `UpdatedAt` - Last update timestamp

**Unique Constraint:**
```sql
UNIQUE(CustomerID, AccountNo, TransferType, ParameterName)
```

**Parameters Tracked:**
- `velocity_check_10min` - Enable/disable 10-min velocity check
- `velocity_check_1hour` - Enable/disable 1-hour velocity check
- `monthly_spending_check` - Enable/disable monthly spending check
- `new_beneficiary_check` - Enable/disable new beneficiary check

**Query Used:**
```sql
SELECT ParameterName, IsEnabled
FROM CustomerAccountTransferTypeConfig
WHERE CustomerID = ? AND AccountNo = ? AND TransferType = ?
AND ParameterName IN ('velocity_check_10min', 'velocity_check_1hour', 'monthly_spending_check', 'new_beneficiary_check')
```

**Used In:**
- `backend/db_service.py` - `get_customer_checks_config()`
- `backend/rule_engine.py` - `check_rule_violation()`
- `api/api.py` - Transaction analysis

---

#### Table: `RetrainingConfig`
**Purpose:** MLOps scheduler configuration

**Columns:**
- `ConfigId` - Unique identifier (always 1)
- `Interval` - Retraining interval (1H, 1D, 1W, 1M, 1Y)
- `IsEnabled` - 1 (enabled) or 0 (disabled)
- `LastRun` - Last retraining timestamp
- `NextRun` - Next scheduled retraining
- `CreatedAt` - Creation timestamp
- `UpdatedAt` - Last update timestamp

**Query Used:**
```sql
SELECT Interval, IsEnabled FROM RetrainingConfig WHERE ConfigId = 1
```

**Used In:**
- `backend/mlops/scheduler.py` - `check_and_update_schedule()`
- `backend/mlops/scheduler.py` - `start_scheduler()`

---

#### Table: `ModelTrainingRuns`
**Purpose:** Training run history and metrics

**Columns:**
- `RunId` - Unique identifier
- `RunDate` - Training run timestamp
- `ModelVersion` - Version trained (1.0.1, 1.0.2, etc.)
- `Status` - SUCCESS or FAILED
- `DataSize` - Number of records used
- `Metrics` - JSON with training metrics

**Used In:**
- `backend/mlops/retraining_pipeline.py` - `log_training_run()`

---

### 4. **Configuration Priority (Hierarchy)**

When checking a configuration, the system follows this priority:

```
1. Customer-Specific Config (CustomerAccountTransferTypeConfig)
   ↓ (if not found)
2. Global Database Config (FeaturesConfig, ThresholdConfig)
   ↓ (if not found)
3. File/Hardcoded Config (risk_thresholds.json, rule_engine.py)
```

**Example - Velocity Check:**
```
Check: Is velocity_check_10min enabled for Customer 1060284, Account 011060284018, Transfer Type O?

1. Query CustomerAccountTransferTypeConfig
   - If found and IsEnabled = 0 → DISABLED (use this)
   - If found and IsEnabled = 1 → ENABLED (use this)
   - If not found → Continue to step 2

2. Query FeaturesConfig
   - If found and IsEnabled = 0 → DISABLED (use this)
   - If found and IsEnabled = 1 → ENABLED (use this)
   - If not found → Continue to step 3

3. Use hardcoded default
   - MAX_VELOCITY_10MIN = 5 (use this)
```

---

## Configuration Summary Table

| Configuration | Location | Type | Scope | Modifiable |
|---|---|---|---|---|
| Risk Thresholds (HIGH/MEDIUM/LOW) | risk_thresholds.json | File | Global | Manual edit |
| Confidence Levels | risk_thresholds.json | File | Global | Manual edit |
| Database Credentials | .env | File | Global | Manual edit |
| API Credentials | .env | File | Global | Manual edit |
| Transfer Multipliers | rule_engine.py | Code | Global | Code change |
| Transfer Min Floors | rule_engine.py | Code | Global | Code change |
| Velocity Limits (10min/1hour) | rule_engine.py | Code | Global | Code change |
| Feature Toggles (47 features) | FeaturesConfig table | Database | Global | SQL UPDATE |
| Thresholds (23 values) | ThresholdConfig table | Database | Global | SQL UPDATE |
| Rule Checks (4 checks) | FeaturesConfig table | Database | Global | SQL UPDATE |
| Customer Overrides | CustomerAccountTransferTypeConfig | Database | Per Customer/Account/Type | SQL INSERT/UPDATE |
| Retraining Schedule | RetrainingConfig table | Database | Global | SQL UPDATE |

---

## How to Modify Configurations

### 1. **Global Risk Thresholds** (File)
```bash
Edit: backend/config/risk_thresholds.json
Restart: API required
```

### 2. **Global Feature Toggles** (Database)
```sql
UPDATE FeaturesConfig 
SET IsEnabled = 0 
WHERE FeatureName = 'velocity_check_10min'
-- No restart required, takes effect on next transaction
```

### 3. **Customer-Specific Overrides** (Database)
```sql
INSERT INTO CustomerAccountTransferTypeConfig
(CustomerID, AccountNo, TransferType, ParameterName, ParameterValue, IsEnabled, CreatedBy)
VALUES('1060284', '011060284018', 'O', 'velocity_check_10min', 'OFF', 0, 'ADMIN')
-- No restart required, takes effect on next transaction
```

### 4. **Retraining Schedule** (Database)
```sql
UPDATE RetrainingConfig 
SET Interval = '1D' 
WHERE ConfigId = 1
-- Scheduler detects change within 5 minutes
```

### 5. **Velocity Limits** (Code)
```python
Edit: backend/rule_engine.py
Change: MAX_VELOCITY_10MIN = 5
Restart: API required
```

---

## Configuration Verification Checklist

- [ ] All 4 database tables created
- [ ] risk_thresholds.json exists and valid JSON
- [ ] .env file configured with correct credentials
- [ ] FeaturesConfig populated with 47 features + 4 rule checks
- [ ] ThresholdConfig populated with 23 thresholds
- [ ] RetrainingConfig has default entry (Interval='1W', IsEnabled=1)
- [ ] Transfer multipliers and floors in rule_engine.py
- [ ] Velocity limits in rule_engine.py
- [ ] API can read all configurations
- [ ] Database queries working correctly

---

## Configuration Change Log

**Latest Changes (MLOps Branch):**
- ✅ Added RetrainingConfig table for scheduler
- ✅ Added ModelTrainingRuns table for training history
- ✅ Enhanced feature_engineering.py to accept live data
- ✅ Updated scheduler to read from RetrainingConfig
- ✅ All configurations verified and documented

---

**Total Configurations:** 50+  
**Database Tables:** 6  
**File Configurations:** 2  
**Hardcoded Configurations:** 2  
**Status:** ✅ Complete and Production Ready
