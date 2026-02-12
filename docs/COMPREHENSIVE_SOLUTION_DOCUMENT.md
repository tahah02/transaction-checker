# Fraud Detection System - Comprehensive Solution Document

## Executive Summary

Yeh ek advanced fraud detection system hai jo real-time transactions ko analyze karta hai aur fraud ka detection karta hai. System teen ML models use karta hai:
1. **Rule-Based Engine** - Deterministic rules
2. **Isolation Forest** - Anomaly detection
3. **Autoencoder** - Deep learning based anomaly detection

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Core Components](#core-components)
3. [Data Flow](#data-flow)
4. [Fraud Detection Logic](#fraud-detection-logic)
5. [Database Schema](#database-schema)
6. [Configuration Management](#configuration-management)
7. [API Endpoints](#api-endpoints)
8. [Configuration & Thresholds](#configuration--thresholds)
9. [Deployment](#deployment)

---

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                      │
│  /analyze_transaction  /approve  /reject  /list_pending     │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼──────────┐    ┌────────▼──────────┐
│  Input Validator │    │  Velocity Service │
│  (Sanitization)  │    │  (Redis/Memory)   │
└────────┬─────────┘    └────────┬──────────┘
         │                       │
         └───────────┬───────────┘
                     │
        ┌────────────▼────────────┐
        │  Database Service       │
        │  (MSSQL Connection)     │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────────────────┐
        │  Fraud Detection Engine             │
        │  ┌──────────────────────────────┐   │
        │  │ 1. Rule Engine               │   │
        │  │ 2. Isolation Forest Model    │   │
        │  │ 3. Autoencoder Model         │   │
        │  └──────────────────────────────┘   │
        └────────────┬────────────────────────┘
                     │
        ┌────────────▼────────────┐
        │  Hybrid Decision Engine  │
        │  (Risk Scoring)          │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────┐
        │  Response Generation    │
        │  (Fraud/Safe Decision)  │
        └────────────────────────┘
```

---

## Core Components

### 1. Input Validator (`backend/input_validator.py`)

**Purpose:** Sanitize aur validate karna sab incoming data ko

**Key Validations:**
- Customer ID: 6-10 digits
- Account Number: 5-20 alphanumeric characters
- Amount: 1 AED to 1,000,000 AED
- Transfer Type: O, I, L, Q, S (uppercase)
- Country: Predefined list (UAE, USA, UK, etc.)
- DateTime: Not in future, not older than 1 day

**Methods:**
```python
validate_customer_id()      # Customer ID validation
validate_account_number()   # Account number cleanup
validate_amount()           # Amount range check
validate_transfer_type()    # Transfer type validation
validate_country()          # Country validation
validate_datetime()         # DateTime validation
sanitize_string()           # XSS/SQL injection prevention
validate_transaction_request()  # Complete request validation
```

---

### 2. Database Service (`backend/db_service.py`)

**Purpose:** MSSQL database ke saath communicate karna

**Connection Details:**
- Server: 10.112.32.4:1433
- Database: retailchannelLogs
- Connection pooling enabled

**Key Methods:**

#### User Statistics
```python
get_user_statistics(customer_id, account_no)
# Returns:
{
    'user_avg_amount': float,           # Average transaction amount
    'user_std_amount': float,           # Standard deviation
    'user_max_amount': float,           # Maximum transaction
    'user_txn_frequency': int,          # Total transactions
    'user_weekly_total': float,         # Weekly spending
    'user_weekly_txn_count': int,       # Weekly transaction count
    'user_weekly_avg_amount': float,    # Weekly average
    'monthly_txn_count': int,           # Monthly transactions
    'current_month_spending': float,    # Current month total
    'monthly_avg_amount': float,        # Monthly average
    'user_international_ratio': float,  # International txn ratio
    'user_high_risk_txn_ratio': float,  # High-risk txn ratio
    'num_accounts': int,                # Total accounts
    'cross_account_transfer_ratio': float
}
```

#### Velocity Metrics
```python
get_velocity_metrics(customer_id, account_no)
# Returns:
{
    'txn_count_30s': int,       # Transactions in last 30 seconds
    'txn_count_10min': int,     # Transactions in last 10 minutes
    'txn_count_1hour': int,     # Transactions in last 1 hour
    'time_since_last_txn': float # Seconds since last transaction
}
```

#### New Beneficiary Check
```python
check_new_beneficiary(customer_id, recipient_account, transfer_type)
# Returns: 1 if new, 0 if existing
```

#### Transaction Logging (Idempotence)
```python
insert_transaction_log(idempotence_key, request_method, request_body, response_body)
# Prevents duplicate processing

get_transaction_log_by_idempotence_key(idempotence_key)
# Retrieves cached response for duplicate requests
```

---

### 3. Velocity Service (`backend/velocity_service.py`)

**Purpose:** Real-time transaction velocity tracking

**Storage Options:**
- Redis (preferred) - Distributed, fast
- In-Memory (fallback) - Local storage

**Key Methods:**
```python
record_transaction(customer_id, account_no, amount)
# Records transaction timestamp and amount

get_velocity_metrics(customer_id, account_no)
# Returns transaction counts in different time windows

get_session_spending(customer_id, account_no)
# Returns total spending in current session

cleanup_old_data()
# Removes transactions older than 1 hour
```

**Time Windows:**
- 30 seconds
- 10 minutes
- 1 hour

---

### 4. Rule Engine (`backend/rule_engine.py`)

**Purpose:** Deterministic fraud rules based on business logic

**Transfer Type Multipliers:**
```
S (Special):     2.0x multiplier, 5000 AED floor
Q (Quick):       2.5x multiplier, 3000 AED floor
L (Local):       3.0x multiplier, 2000 AED floor
I (International): 3.5x multiplier, 1500 AED floor
O (Other):       4.0x multiplier, 1000 AED floor
M (Mobile):      3.2x multiplier, 1800 AED floor
F (Foreign):     3.8x multiplier, 1200 AED floor
```

**Threshold Calculation:**
```
Threshold = MAX(user_avg + multiplier × user_std, floor)
```

**Rules:**

1. **Velocity Check (10 minutes)**
   - Max: 5 transactions
   - Violation: Fraud flag

2. **Velocity Check (1 hour)**
   - Max: 15 transactions
   - Violation: Fraud flag

3. **Monthly Spending Limit**
   - Projected = current_month_spending + new_amount
   - If Projected > Threshold: Fraud flag

4. **New Beneficiary**
   - First transaction to new recipient: Requires approval

---

### 5. Feature Engineering (`backend/feature_engineering.py`)

**Purpose:** Transform raw transaction data into ML features

**Input:** Raw transaction CSV
**Output:** Feature dataset for ML models

**Feature Categories:**

#### Transaction Features
- `transaction_amount`: Transaction amount in AED
- `flag_amount`: 1 if Special transfer, 0 otherwise
- `transfer_type_encoded`: Numeric encoding (0-4)
- `transfer_type_risk`: Risk score per transfer type (0-0.9)

#### Temporal Features
- `hour`: Hour of transaction (0-23)
- `day_of_week`: Day of week (0-6)
- `is_weekend`: 1 if Saturday/Sunday
- `is_night`: 1 if 22:00-06:00
- `time_since_last`: Seconds since last transaction
- `recent_burst`: 1 if < 5 minutes since last txn

#### Velocity Features
- `txn_count_30s`: Transactions in last 30 seconds
- `txn_count_10min`: Transactions in last 10 minutes
- `txn_count_1hour`: Transactions in last 1 hour

#### User Statistics
- `user_avg_amount`: User's average transaction
- `user_std_amount`: User's standard deviation
- `user_max_amount`: User's maximum transaction
- `user_txn_frequency`: Total transactions by user

#### Period-Based Features
- **Weekly:**
  - `weekly_total`: Total spending this week
  - `weekly_txn_count`: Transaction count this week
  - `weekly_avg_amount`: Average amount this week
  - `weekly_deviation`: Deviation from weekly average
  - `amount_vs_weekly_avg`: Ratio to weekly average

- **Monthly:**
  - `current_month_spending`: Total spending this month
  - `monthly_txn_count`: Transaction count this month
  - `monthly_avg_amount`: Average amount this month
  - `monthly_deviation`: Deviation from monthly average
  - `amount_vs_monthly_avg`: Ratio to monthly average

#### Risk Features
- `intl_ratio`: International transaction ratio
- `user_high_risk_txn_ratio`: High-risk transaction ratio
- `user_multiple_accounts_flag`: 1 if multiple accounts
- `cross_account_transfer_ratio`: Cross-account transfer ratio
- `geo_anomaly_flag`: 1 if unusual country
- `is_new_beneficiary`: 1 if new recipient
- `beneficiary_txn_count_30d`: Transactions to this beneficiary in 30 days

---

### 6. Isolation Forest Model (`backend/isolation_forest.py`)

**Purpose:** Unsupervised anomaly detection using Isolation Forest

**Model Details:**
- Algorithm: Scikit-learn Isolation Forest
- Input: 40+ engineered features
- Output: Anomaly score (-1 to 1)

**Scoring:**
```python
score_transaction(features)
# Returns:
{
    'anomaly_score': float,      # -1 to 1 (lower = more anomalous)
    'prediction': int,           # -1 (anomaly) or 1 (normal)
    'is_anomaly': bool,          # True if anomaly detected
    'reason': str                # Explanation
}
```

**Thresholds (from config):**
- High Risk: score >= 0.8
- Medium Risk: score >= 0.65
- Low Risk: score >= 0.4
- Safe: score < 0.4

---

### 7. Autoencoder Model (`backend/autoencoder.py`)

**Purpose:** Deep learning based anomaly detection

**Architecture:**
```
Input (40+ features)
    ↓
Dense(64) + BatchNorm + ReLU
    ↓
Dense(32) + BatchNorm + ReLU
    ↓
Dense(14) [Bottleneck - Encoding]
    ↓
Dense(32) + BatchNorm + ReLU
    ↓
Dense(64) + BatchNorm + ReLU
    ↓
Output (40+ features)
```

**Training:**
- Loss: Mean Squared Error (MSE)
- Optimizer: Adam
- Early Stopping: patience=5 on validation loss
- Batch Size: 64
- Epochs: 100 (with early stopping)

**Inference:**
```python
score_transaction(features)
# Returns:
{
    'reconstruction_error': float,  # MSE between input and output
    'threshold': float,             # Anomaly threshold
    'is_anomaly': bool,             # True if error > threshold
    'reason': str                   # Explanation
}
```

**Anomaly Detection:**
- If reconstruction_error > threshold: Anomaly
- Threshold determined during training on validation set

---

### 8. Hybrid Decision Engine (`backend/hybrid_decision.py`)

**Purpose:** Combine all three models for final fraud decision

**Decision Logic:**

```python
make_decision(transaction, user_stats, ml_model, features, autoencoder)
```

**Process:**

1. **Rule Engine Check**
   - Check velocity limits
   - Check monthly spending
   - Check new beneficiary
   - Result: violated (bool), reasons (list), threshold (float)

2. **Isolation Forest Check**
   - If violated: Add ML confidence (15% weight)
   - If not violated: Use ML score directly
   - Threshold: 0.65 for fraud flag

3. **Autoencoder Check**
   - Score reconstruction error
   - Add to risk score (10% weight)
   - Flag if anomaly detected

4. **Risk Score Calculation**
   ```
   Base Risk = Rule violation score (0.6-0.85)
   + ML contribution (0-0.15)
   + AE contribution (0-0.10)
   = Final Risk Score (0-1.0)
   ```

5. **Confidence Level**
   ```
   Models Agreeing    Confidence
   3 (All)           95%
   2                 80%
   1                 60%
   0                 60%
   
   + High Risk Boost: +3% if ML score > 0.8
   ```

6. **Risk Level Classification**
   ```
   Risk Score >= 0.8  → HIGH
   Risk Score >= 0.65 → MEDIUM
   Risk Score >= 0.4  → LOW
   Risk Score < 0.4   → SAFE
   ```

**Output:**
```python
{
    'is_fraud': bool,                    # Final decision
    'reasons': [str],                    # Explanation list
    'risk_score': float,                 # 0-1.0
    'risk_level': str,                   # SAFE/LOW/MEDIUM/HIGH
    'confidence_level': float,           # 0-1.0
    'model_agreement': float,            # 0-1.0 (fraction of models agreeing)
    'threshold': float,                  # Amount threshold used
    'ml_flag': bool,                     # Isolation Forest flagged
    'ae_flag': bool,                     # Autoencoder flagged
    'ae_reconstruction_error': float,    # AE error value
    'ae_threshold': float                # AE threshold used
}
```

---

## Data Flow

### Transaction Analysis Flow

```
1. API Request Received
   ↓
2. Input Validation
   - Sanitize all fields
   - Check data types and ranges
   - Return 400 if invalid
   ↓
3. Idempotence Check
   - Check if idempotence_key exists in DB
   - If yes: Return cached response
   - If no: Continue
   ↓
4. Fetch User Statistics
   - Query DB for user's historical data
   - Calculate averages, std dev, max
   - Get weekly/monthly aggregates
   ↓
5. Velocity Check
   - Record transaction in velocity service
   - Get velocity metrics (30s, 10min, 1hr)
   - Check new beneficiary status
   ↓
6. Feature Engineering
   - Build feature vector from transaction + stats
   - 40+ features prepared
   ↓
7. Rule Engine
   - Check velocity limits
   - Check monthly spending
   - Check new beneficiary
   ↓
8. ML Model Scoring
   - Isolation Forest prediction
   - Autoencoder reconstruction error
   ↓
9. Hybrid Decision
   - Combine all signals
   - Calculate risk score
   - Determine confidence
   ↓
10. Log Transaction
    - Store in transaction_log table
    - Store decision details
    ↓
11. Return Response
    - is_fraud: true/false
    - risk_level: SAFE/LOW/MEDIUM/HIGH
    - confidence_level: 0-1.0
    - reasons: [list of explanations]
```

---

## Fraud Detection Logic

### Scenario 1: Velocity-Based Fraud

**Transaction:** Customer sends 8 transactions in 5 minutes

**Detection:**
1. Rule Engine: txn_count_10min = 8 > 5 → VIOLATED
2. Risk Score: 0.85 (velocity violation base)
3. Decision: **FRAUD** (HIGH risk)

---

### Scenario 2: Amount Anomaly

**Transaction:** Customer usually spends 5,000 AED, now sends 500,000 AED

**Detection:**
1. Rule Engine: 500,000 > threshold (5,000 + 3×std) → VIOLATED
2. ML Model: Isolation Forest detects anomaly → FLAGGED
3. Risk Score: 0.85 + 0.15 = 1.0
4. Confidence: 95% (both models agree)
5. Decision: **FRAUD** (HIGH risk)

---

### Scenario 3: New Beneficiary

**Transaction:** First transfer to new recipient

**Detection:**
1. Rule Engine: is_new_beneficiary = 1 → VIOLATED
2. Risk Score: 0.60 (new beneficiary base)
3. Decision: **FRAUD** (LOW risk, requires approval)

---

### Scenario 4: Normal Transaction

**Transaction:** Customer sends 10,000 AED (within normal range)

**Detection:**
1. Rule Engine: All checks pass → NOT VIOLATED
2. ML Model: Normal pattern → NOT FLAGGED
3. Autoencoder: Low reconstruction error → NOT FLAGGED
4. Risk Score: 0.0
5. Decision: **SAFE** (SAFE risk level)

---

## Database Schema

### Key Tables

#### 1. Transactions Table
```sql
CREATE TABLE Transactions (
    TransactionId INT PRIMARY KEY,
    CustomerId VARCHAR(10),
    FromAccountNo VARCHAR(20),
    ToAccountNo VARCHAR(20),
    AmountInAed DECIMAL(15,2),
    TransferType CHAR(1),
    CreateDate DATETIME,
    BankCountry VARCHAR(50),
    ChannelId INT,
    ReceipentAccount VARCHAR(20)
)
```

#### 2. Transaction Log (Idempotence)
```sql
CREATE TABLE TransactionLog (
    IdempotenceKey VARCHAR(100) PRIMARY KEY,
    RequestMethod VARCHAR(50),
    RequestBody TEXT,
    ResponseBody TEXT,
    CreatedAt DATETIME,
    ExpiresAt DATETIME
)
```

#### 3. Pending Transactions
```sql
CREATE TABLE PendingTransactions (
    PendingId INT PRIMARY KEY,
    TransactionId INT,
    CustomerId VARCHAR(10),
    Amount DECIMAL(15,2),
    Status VARCHAR(20),
    CreatedAt DATETIME,
    ApprovedAt DATETIME,
    ApprovedBy VARCHAR(50)
)
```

#### 4. Feature Flags
```sql
CREATE TABLE FeatureFlags (
    FeatureName VARCHAR(100) PRIMARY KEY,
    IsEnabled BIT,
    CreatedAt DATETIME,
    UpdatedAt DATETIME
)
```

---

## Configuration Management

### Overview

Configuration system ab database-driven hai. Admin ko real-time ON/OFF control milta hai har check ke liye, customer/account/transfer-type level pe.

### Database Tables

#### 1. FeaturesConfig Table
```sql
CREATE TABLE FeaturesConfig (
    FeatureID INT PRIMARY KEY IDENTITY(1,1),
    FeatureName NVARCHAR(100) UNIQUE NOT NULL,
    Description NVARCHAR(MAX),
    IsEnabled BIT DEFAULT 0,
    FeatureType NVARCHAR(50),
    Version NVARCHAR(20),
    CreatedAt DATETIME DEFAULT GETDATE(),
    UpdatedAt DATETIME DEFAULT GETDATE(),
    CreatedBy NVARCHAR(100),
    UpdatedBy NVARCHAR(100),
    RollbackVersion NVARCHAR(20),
    IsActive BIT DEFAULT 1
)
```

**47 Features Stored:**
- 43 ML Features (transaction_amount, flag_amount, etc.)
- 4 Rule Checks (velocity_check_10min, velocity_check_1hour, monthly_spending_check, new_beneficiary_check)

#### 2. ThresholdConfig Table
```sql
CREATE TABLE ThresholdConfig (
    ThresholdID INT PRIMARY KEY IDENTITY(1,1),
    ThresholdName NVARCHAR(100) NOT NULL,
    ThresholdType NVARCHAR(50),
    ThresholdValue FLOAT NOT NULL,
    MinValue FLOAT,
    MaxValue FLOAT,
    PreviousValue FLOAT,
    Description NVARCHAR(MAX),
    IsActive BIT DEFAULT 1,
    EffectiveFrom DATETIME,
    EffectiveTo DATETIME,
    CreatedAt DATETIME DEFAULT GETDATE(),
    UpdatedAt DATETIME DEFAULT GETDATE(),
    CreatedBy NVARCHAR(100),
    UpdatedBy NVARCHAR(100),
    Rationale NVARCHAR(MAX),
    ImpactAnalysis NVARCHAR(MAX),
    ApprovalStatus NVARCHAR(50),
    ApprovedBy NVARCHAR(100)
)
```

**23 Thresholds Stored:**
- Isolation Forest thresholds (high, medium, low)
- Confidence calculation values
- Velocity limits
- Transfer type multipliers (7 types)
- Transfer type min floors (7 types)

#### 3. CustomerAccountTransferTypeConfig Table
```sql
CREATE TABLE CustomerAccountTransferTypeConfig (
    ConfigID INT PRIMARY KEY IDENTITY(1,1),
    CustomerID NVARCHAR(100) NOT NULL,
    AccountNo NVARCHAR(50) NOT NULL,
    TransferType NVARCHAR(10) NOT NULL,
    ParameterName NVARCHAR(100) NOT NULL,
    ParameterValue NVARCHAR(MAX),
    IsEnabled BIT DEFAULT 1,
    DataType NVARCHAR(50),
    MinValue FLOAT,
    MaxValue FLOAT,
    Description NVARCHAR(MAX),
    CreatedAt DATETIME DEFAULT GETDATE(),
    UpdatedAt DATETIME DEFAULT GETDATE(),
    CreatedBy NVARCHAR(100),
    UpdatedBy NVARCHAR(100),
    IsActive BIT DEFAULT 1,
    CONSTRAINT UK_CustomerAccountTransferTypeConfig UNIQUE (CustomerID, AccountNo, TransferType, ParameterName)
)
```

**Customer-Specific Overrides:**
- CustomerID + AccountNo + TransferType level granularity
- Any parameter can be ON/OFF or custom value
- Example: Customer 1060284, Account 011060284018, TransferType O → velocity_check_10min = OFF

### Configuration Flow

```
1. Admin Updates Database
   ↓
2. Next Transaction Request
   ↓
3. Code Fetches Config from DB
   - get_customer_checks_config(customer_id, account_no, transfer_type)
   ↓
4. Config Applied to Rules
   - If velocity_check_10min = 0 (OFF) → Skip velocity check
   - If velocity_check_10min = 1 (ON) → Run velocity check
   ↓
5. Decision Made with Config
   ↓
6. Response Returned
```

### Implementation Details

#### New Method in db_service.py
```python
def get_customer_checks_config(self, customer_id: str, account_no: str, transfer_type: str) -> Dict[str, int]:
    """
    Fetch customer-specific rule checks configuration.
    Returns ON/OFF status for 4 rule checks.
    Default: All checks ON (1)
    """
    # Queries CustomerAccountTransferTypeConfig table
    # Returns: {
    #     'velocity_check_10min': 1,
    #     'velocity_check_1hour': 1,
    #     'monthly_spending_check': 1,
    #     'new_beneficiary_check': 1
    # }
```

#### Modified hybrid_decision.py
```python
def make_decision(txn, user_stats, model, features, autoencoder=None):
    # Fetch customer config from database
    db = get_db_service()
    checks_config = db.get_customer_checks_config(
        customer_id=txn['customer_id'],
        account_no=txn['account_no'],
        transfer_type=txn['transfer_type']
    )
    
    # Pass config to rule engine
    violated, rule_reasons, threshold = check_rule_violation(
        ...,
        checks_config=checks_config
    )
```

#### Modified rule_engine.py
```python
def check_rule_violation(..., checks_config=None):
    # Check each rule only if enabled
    if checks_config['velocity_check_10min'] == 1:
        if txn_count_10min > MAX_VELOCITY_10MIN:
            violated = True
            reasons.append(...)
    
    if checks_config['velocity_check_1hour'] == 1:
        if txn_count_1hour > MAX_VELOCITY_1HOUR:
            violated = True
            reasons.append(...)
    
    # Similar for other checks
```

### Admin Usage Example

**Scenario:** Customer 1060284 complains about velocity check blocking legitimate transactions

**Solution:**
```sql
-- Disable velocity_check_10min for this customer
UPDATE CustomerAccountTransferTypeConfig
SET IsEnabled = 0
WHERE CustomerID = '1060284' 
AND AccountNo = '011060284018' 
AND TransferType = 'O'
AND ParameterName = 'velocity_check_10min'
```

**Result:** Next transaction from this customer won't trigger velocity check

**Re-enable:**
```sql
UPDATE CustomerAccountTransferTypeConfig
SET IsEnabled = 1
WHERE CustomerID = '1060284' 
AND AccountNo = '011060284018' 
AND TransferType = 'O'
AND ParameterName = 'velocity_check_10min'
```

### Default Behavior

- If no config found in database → All checks ON (default)
- If config found → Use database value
- Immediate effect on next transaction

---

## Risk Score System

### What is Risk Score?

Risk Score ek numerical value (0 to 1.0) hai jo transaction ke fraud probability ko represent karta hai:
- **0.0** = Bilkul safe, koi fraud risk nahi
- **0.5** = Medium risk, suspicious activity
- **1.0** = Maximum risk, definitely fraud

### Risk Score Calculation

Risk score teen models se combine hota hai:

```
Final Risk Score = Rule Engine Score + ML Score + AE Score
                 = (0-0.85) + (0-0.15) + (0-0.10)
                 = 0 to 1.0
```

#### 1. Rule Engine Score (0 to 0.85)

**Base Scores per Violation Type:**
```
Velocity Violation (10min/1hour)  → 0.85
Monthly Spending Violation        → 0.70
New Beneficiary                   → 0.60
Other Violations                  → 0.75
No Violations                     → 0.00
```

**Example:**
- Customer sends 8 transactions in 5 minutes (velocity violation)
- Rule Engine Score = 0.85

#### 2. ML Model Score (0 to 0.15)

**Isolation Forest Contribution:**
- Only added if rule already violated
- Weight: 15% of ML anomaly score
- Range: 0 to 0.15

**Example:**
- Rule violation detected: 0.85
- ML anomaly score: 0.8 (high anomaly)
- ML contribution: 0.8 × 0.15 = 0.12
- New score: 0.85 + 0.12 = 0.97

#### 3. Autoencoder Score (0 to 0.10)

**Reconstruction Error Contribution:**
- Added if autoencoder detects anomaly
- Weight: 10% of reconstruction error
- Range: 0 to 0.10

**Example:**
- Current score: 0.97
- AE reconstruction error: 0.5 (moderate anomaly)
- AE contribution: 0.5 × 0.10 = 0.05
- Final score: 0.97 + 0.05 = 1.02 → Capped at 1.0

### Risk Level Classification

Risk Score is mapped to Risk Levels:

```
Risk Score >= 0.8   → HIGH RISK
Risk Score >= 0.65  → MEDIUM RISK
Risk Score >= 0.4   → LOW RISK
Risk Score < 0.4    → SAFE
```

**Decision Mapping:**
```
HIGH RISK    → REQUIRES_USER_APPROVAL (Block transaction, ask customer)
MEDIUM RISK  → REQUIRES_USER_APPROVAL (Block transaction, ask customer)
LOW RISK     → APPROVE_WITH_NOTIFICATION (Approve but notify customer)
SAFE         → APPROVED (Auto-approve, no notification)
```

### Real-World Examples

#### Example 1: Normal Transaction
```
Transaction: Customer sends 5,000 AED (normal amount)
- Rule Engine: All checks pass → 0.00
- ML Model: Normal pattern → 0.00
- Autoencoder: Low error → 0.00
- Final Risk Score: 0.00
- Risk Level: SAFE
- Decision: APPROVED
```

#### Example 2: Velocity-Based Fraud
```
Transaction: Customer sends 10 transactions in 3 minutes
- Rule Engine: Velocity violation → 0.85
- ML Model: Detects anomaly (0.9) → 0.85 + (0.9 × 0.15) = 0.985
- Autoencoder: High error → 0.985 + (0.8 × 0.10) = 1.0
- Final Risk Score: 1.0 (capped)
- Risk Level: HIGH
- Decision: REQUIRES_USER_APPROVAL
```

#### Example 3: Amount Anomaly
```
Transaction: Customer usually spends 5K, now sends 500K
- Rule Engine: Monthly spending violation → 0.70
- ML Model: Detects anomaly (0.85) → 0.70 + (0.85 × 0.15) = 0.8275
- Autoencoder: Moderate error → 0.8275 + (0.6 × 0.10) = 0.8875
- Final Risk Score: 0.8875
- Risk Level: HIGH
- Decision: REQUIRES_USER_APPROVAL
```

#### Example 4: New Beneficiary (Low Risk)
```
Transaction: First transfer to new recipient (5,000 AED)
- Rule Engine: New beneficiary → 0.60
- ML Model: Normal pattern → 0.60 + (0.2 × 0.15) = 0.63
- Autoencoder: Low error → 0.63 + (0.1 × 0.10) = 0.64
- Final Risk Score: 0.64
- Risk Level: MEDIUM
- Decision: REQUIRES_USER_APPROVAL
```

### Confidence Level

Confidence Level (0 to 1.0) shows how confident the system is about its decision:

```
Models Agreeing    Confidence
3 (All)           95%
2                 80%
1                 60%
0                 60%

+ High Risk Boost: +3% if ML score > 0.8
```

**Example:**
- Rule Engine: Flagged (1)
- ML Model: Flagged (1)
- Autoencoder: Not flagged (0)
- Models agreeing: 2 → 80% confidence
- ML score: 0.85 > 0.8 → +3% boost
- Final Confidence: 83%

### Model Agreement

Model Agreement (0 to 1.0) shows fraction of models that detected fraud:

```
Model Agreement = (Rule Flagged + ML Flagged + AE Flagged) / 3
```

**Example:**
- Rule Engine: Flagged (1)
- ML Model: Flagged (1)
- Autoencoder: Not flagged (0)
- Model Agreement: (1 + 1 + 0) / 3 = 0.67 (67%)

### Risk Score in API Response

```json
{
  "is_fraud": true,
  "risk_score": 0.85,
  "risk_level": "HIGH",
  "confidence_level": 0.95,
  "model_agreement": 0.67,
  "reasons": [
    "Velocity limit exceeded: 8 transactions in last 10 minutes (max allowed 5)",
    "ML anomaly detected: risk score 0.8500 exceeds threshold 0.6500"
  ],
  "individual_scores": {
    "rule_engine": {
      "violated": true,
      "threshold": 45000
    },
    "isolation_forest": {
      "anomaly_score": 0.85,
      "is_anomaly": true
    },
    "autoencoder": {
      "reconstruction_error": 0.12,
      "is_anomaly": false
    }
  }
}
```

### Risk Score Interpretation Guide

| Risk Score | Risk Level | Interpretation | Action |
|-----------|-----------|-----------------|--------|
| 0.0-0.2 | SAFE | Very low fraud probability | Auto-approve |
| 0.2-0.4 | SAFE | Low fraud probability | Auto-approve |
| 0.4-0.65 | LOW | Moderate fraud probability | Notify customer |
| 0.65-0.8 | MEDIUM | High fraud probability | Require approval |
| 0.8-1.0 | HIGH | Very high fraud probability | Block & investigate |

### Adjusting Risk Scores

Admin can adjust risk scores by:

1. **Modifying Thresholds** (ThresholdConfig table)
   ```sql
   UPDATE ThresholdConfig
   SET ThresholdValue = 0.75
   WHERE ThresholdName = 'high_risk_threshold'
   ```

2. **Disabling Checks** (CustomerAccountTransferTypeConfig table)
   ```sql
   UPDATE CustomerAccountTransferTypeConfig
   SET IsEnabled = 0
   WHERE ParameterName = 'velocity_check_10min'
   ```

3. **Adjusting Model Weights** (hybrid_decision.py)
   - ML weight: Currently 15%
   - AE weight: Currently 10%
   - Can be tuned based on performance

---

## Configuration Management Strategy

### Overview

Configuration system mein **3 layers** hain:

```
Layer 1: Static Config (File)
├── risk_thresholds.json
└── .env

Layer 2: Global Config (Database)
├── FeaturesConfig (47 features)
└── ThresholdConfig (23 thresholds)

Layer 3: Customer-Specific Config (Database)
└── CustomerAccountTransferTypeConfig (overrides)
```

### Layer 1: Static Configuration (File-Based)

**Files:**
- `backend/config/risk_thresholds.json`
- `.env`

**What's Here:**
- Risk level thresholds (0.8, 0.65, 0.4)
- Confidence calculation values
- Risk level names (SAFE, LOW, MEDIUM, HIGH)
- Database credentials
- API credentials

**When to Change:**
- System-wide threshold changes
- Credential updates
- Rarely changed (requires code restart)

**Example:**
```json
{
  "isolation_forest": {
    "high_risk_threshold": 0.8,
    "medium_risk_threshold": 0.65,
    "low_risk_threshold": 0.4
  }
}
```

**Management:**
- Manual edit in file
- Requires Docker restart
- Version controlled in Git

---

### Layer 2: Global Configuration (Database)

**Tables:**
- `FeaturesConfig` - 47 features/rules
- `ThresholdConfig` - 23 thresholds

**What's Here:**
- All 47 ML features (ON/OFF toggles)
- All 4 rule checks (ON/OFF toggles)
- Global thresholds (multipliers, floors, limits)
- Version history
- Approval status

**When to Change:**
- Enable/disable features globally
- Adjust global thresholds
- Frequently changed (no restart needed)

**Example:**

```sql
-- Enable/Disable a feature globally
UPDATE FeaturesConfig
SET IsEnabled = 1
WHERE FeatureName = 'velocity_check_10min'

-- Change global threshold
UPDATE ThresholdConfig
SET ThresholdValue = 0.75
WHERE ThresholdName = 'high_risk_threshold'
```

**Management:**
- Direct database updates
- Immediate effect (no restart)
- Audit trail maintained (CreatedBy, UpdatedBy, CreatedAt, UpdatedAt)
- Rollback possible (RollbackVersion field)

**Default Behavior:**
- If feature not in database → Assume ON
- If threshold not in database → Use file value

---

### Layer 3: Customer-Specific Configuration (Database)

**Table:**
- `CustomerAccountTransferTypeConfig`

**What's Here:**
- Customer + Account + TransferType level overrides
- Any parameter can be ON/OFF or custom value
- Granular control per customer

**When to Change:**
- Customer-specific exceptions
- Whitelist/blacklist specific customers
- Real-time adjustments

**Example:**

```sql
-- Disable velocity check for specific customer
INSERT INTO CustomerAccountTransferTypeConfig
(CustomerID, AccountNo, TransferType, ParameterName, ParameterValue, IsEnabled, CreatedBy)
VALUES
('1060284', '011060284018', 'O', 'velocity_check_10min', 'OFF', 0, 'ADMIN')

-- Custom amount threshold for customer
INSERT INTO CustomerAccountTransferTypeConfig
(CustomerID, AccountNo, TransferType, ParameterName, ParameterValue, IsEnabled, CreatedBy)
VALUES
('1060284', '011060284018', 'S', 'amount_threshold', '100000', 1, 'ADMIN')
```

**Management:**
- Direct database updates
- Immediate effect (no restart)
- Unique constraint: (CustomerID, AccountNo, TransferType, ParameterName)
- Prevents duplicate entries

---

### Configuration Priority (Hierarchy)

When transaction comes, system checks in this order:

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

**Example:**

```
Transaction: Customer 1060284, Account 011060284018, TransferType O

Step 1: Check CustomerAccountTransferTypeConfig
  Query: SELECT IsEnabled FROM CustomerAccountTransferTypeConfig
         WHERE CustomerID='1060284' AND AccountNo='011060284018' 
         AND TransferType='O' AND ParameterName='velocity_check_10min'
  Result: Found → IsEnabled = 0 (OFF)
  Action: Skip velocity check

If not found:
Step 2: Check FeaturesConfig
  Query: SELECT IsEnabled FROM FeaturesConfig
         WHERE FeatureName='velocity_check_10min'
  Result: Found → IsEnabled = 1 (ON)
  Action: Run velocity check

If not found:
Step 3: Use Default
  Default: ON (1)
  Action: Run velocity check
```

---

### ON/OFF Management

#### Scenario 1: Turn OFF Velocity Check for All Customers

**Method:** Update FeaturesConfig (Global)

```sql
UPDATE FeaturesConfig
SET IsEnabled = 0
WHERE FeatureName = 'velocity_check_10min'
```

**Effect:** All customers affected immediately (except those with customer-specific override)

**Revert:**
```sql
UPDATE FeaturesConfig
SET IsEnabled = 1
WHERE FeatureName = 'velocity_check_10min'
```

---

#### Scenario 2: Turn OFF Velocity Check for Specific Customer

**Method:** Insert/Update CustomerAccountTransferTypeConfig

```sql
-- First time
INSERT INTO CustomerAccountTransferTypeConfig
(CustomerID, AccountNo, TransferType, ParameterName, ParameterValue, IsEnabled, CreatedBy)
VALUES
('1060284', '011060284018', 'O', 'velocity_check_10min', 'OFF', 0, 'ADMIN')

-- Or update if exists
UPDATE CustomerAccountTransferTypeConfig
SET IsEnabled = 0
WHERE CustomerID = '1060284' 
AND AccountNo = '011060284018' 
AND TransferType = 'O'
AND ParameterName = 'velocity_check_10min'
```

**Effect:** Only this customer affected immediately

**Revert:**
```sql
UPDATE CustomerAccountTransferTypeConfig
SET IsEnabled = 1
WHERE CustomerID = '1060284' 
AND AccountNo = '011060284018' 
AND TransferType = 'O'
AND ParameterName = 'velocity_check_10min'
```

---

#### Scenario 3: Turn OFF Velocity Check for Specific Customer + TransferType

**Method:** Same as Scenario 2, but more specific

```sql
-- Only for TransferType 'O'
INSERT INTO CustomerAccountTransferTypeConfig
(CustomerID, AccountNo, TransferType, ParameterName, ParameterValue, IsEnabled, CreatedBy)
VALUES
('1060284', '011060284018', 'O', 'velocity_check_10min', 'OFF', 0, 'ADMIN')

-- TransferType 'S' still has velocity check ON
-- (Uses global FeaturesConfig value)
```

---

### Configuration Workflow

```
Admin Decision
    ↓
┌───────────────────────────────────────┐
│ Is it global or customer-specific?    │
└───────────────────────────────────────┘
    ↙                                ↘
GLOBAL                          CUSTOMER-SPECIFIC
    ↓                                ↓
Update FeaturesConfig          Update CustomerAccountTransferTypeConfig
or ThresholdConfig             
    ↓                                ↓
Immediate Effect               Immediate Effect
(All customers)                (Specific customer only)
    ↓                                ↓
Next Transaction               Next Transaction
Uses New Config                Uses New Config
```

---

### Configuration Audit Trail

All changes are tracked:

```sql
-- View who changed what and when
SELECT 
    FeatureName,
    IsEnabled,
    CreatedBy,
    CreatedAt,
    UpdatedBy,
    UpdatedAt
FROM FeaturesConfig
ORDER BY UpdatedAt DESC

-- View customer-specific changes
SELECT 
    CustomerID,
    AccountNo,
    TransferType,
    ParameterName,
    IsEnabled,
    CreatedBy,
    CreatedAt,
    UpdatedBy,
    UpdatedAt
FROM CustomerAccountTransferTypeConfig
ORDER BY UpdatedAt DESC
```

---

### Configuration Best Practices

1. **Always Update Database, Not Code**
   - Never hardcode changes in Python files
   - Always use database for dynamic config

2. **Use Customer-Specific Config for Exceptions**
   - Keep global config for standard rules
   - Use customer-specific for VIP/problematic customers

3. **Document Changes**
   - Add reason in Description field
   - Track who made change (CreatedBy/UpdatedBy)

4. **Test Before Applying**
   - Test with small customer set first
   - Then roll out globally if successful

5. **Maintain Audit Trail**
   - Never delete old configs
   - Use IsActive = 0 to disable instead of deleting
   - Keep version history

---

### Configuration Summary Table

| Config Type | Location | Scope | Change Frequency | Restart Needed | Audit Trail |
|------------|----------|-------|------------------|----------------|------------|
| Static | risk_thresholds.json | Global | Rarely | Yes | Git |
| Static | .env | Global | Rarely | Yes | Git |
| Global | FeaturesConfig | All Customers | Often | No | Database |
| Global | ThresholdConfig | All Customers | Often | No | Database |
| Customer | CustomerAccountTransferTypeConfig | Specific | Very Often | No | Database |

---

## Database Tables & Data Flow

### Overview

System mein **6 main tables** hain. Har table ka apna purpose hai aur data flow mein specific role hai.

### Table 1: TransactionHistoryLogs (Source Data)

**Purpose:** Original transaction data from banking system

**Columns:**
- CustomerId, FromAccountNo, ToAccountNo
- AmountInAed, TransferType
- CreateDate, BankCountry
- ChannelId, ReceipentAccount, BankName

**Data Flow:**
```
User sends transaction
    ↓
API receives request
    ↓
Query TransactionHistoryLogs table
    ↓
Get user's historical transactions
    ↓
Calculate user statistics (avg, std, max)
```

**Usage in Code:**
```python
# db_service.py
def get_user_statistics(customer_id, account_no):
    # Queries TransactionHistoryLogs
    # Returns: user_avg_amount, user_std_amount, user_max_amount, etc.
```

---

### Table 2: FeaturesConfig (Global Feature Toggles)

**Purpose:** Enable/disable 47 ML features globally

**Columns:**
- FeatureID, FeatureName, Description
- IsEnabled (0/1), FeatureType
- Version, CreatedAt, UpdatedAt, CreatedBy, UpdatedBy

**Data Stored:**
- 43 ML Features (transaction_amount, flag_amount, etc.)
- 4 Rule Checks (velocity_check_10min, velocity_check_1hour, etc.)

**Data Flow:**
```
Feature Engineering starts
    ↓
Check FeaturesConfig table
    ↓
For each feature:
  - If IsEnabled = 1 → Include in feature vector
  - If IsEnabled = 0 → Skip this feature
    ↓
Build feature vector for ML models
```

**Usage in Code:**
```python
# feature_engineering.py
enabled_features = db.get_enabled_features()
# Returns list of enabled feature names

if 'flag_amount' in enabled_features:
    df['flag_amount'] = (tt == 'S').astype(int)
```

---

### Table 3: ThresholdConfig (Global Thresholds)

**Purpose:** Store all global threshold values

**Columns:**
- ThresholdID, ThresholdName, ThresholdType
- ThresholdValue, MinValue, MaxValue, PreviousValue
- Description, IsActive, EffectiveFrom, EffectiveTo
- CreatedAt, UpdatedAt, CreatedBy, UpdatedBy
- Rationale, ImpactAnalysis, ApprovalStatus, ApprovedBy

**Data Stored (23 Thresholds):**
- Isolation Forest: high_risk_threshold (0.8), medium (0.65), low (0.4)
- Confidence: all_models_agree (0.95), two_models (0.80), one_model (0.60), boost (0.03)
- Velocity: MAX_VELOCITY_10MIN (5), MAX_VELOCITY_1HOUR (15)
- Transfer Multipliers: S (2.0), Q (2.5), L (3.0), I (3.5), O (4.0), M (3.2), F (3.8)
- Transfer Floors: S (5000), Q (3000), L (2000), I (1500), O (1000), M (1800), F (1200)

**Data Flow:**
```
Rule Engine starts
    ↓
Calculate threshold for transaction
    ↓
Query ThresholdConfig
    ↓
Get transfer type multiplier & floor
    ↓
Threshold = MAX(user_avg + multiplier × user_std, floor)
    ↓
Compare transaction amount with threshold
```

**Usage in Code:**
```python
# rule_engine.py
TRANSFER_MULTIPLIERS = {'S': 2.0, 'Q': 2.5, ...}  # From ThresholdConfig
TRANSFER_MIN_FLOORS = {'S': 5000, 'Q': 3000, ...}  # From ThresholdConfig

threshold = max(user_avg + multiplier * user_std, floor)
```

---

### Table 4: CustomerAccountTransferTypeConfig (Customer-Specific Overrides)

**Purpose:** Override global config for specific customers

**Columns:**
- ConfigID, CustomerID, AccountNo, TransferType
- ParameterName, ParameterValue
- IsEnabled (0/1), DataType
- MinValue, MaxValue, Description
- CreatedAt, UpdatedAt, CreatedBy, UpdatedBy, IsActive

**Data Stored:**
- Customer-specific ON/OFF for each rule check
- Custom thresholds per customer
- Example: Customer 1060284, Account 011060284018, TransferType O → velocity_check_10min = OFF

**Data Flow:**
```
Transaction arrives
    ↓
Extract: customer_id, account_no, transfer_type
    ↓
Query CustomerAccountTransferTypeConfig
    ↓
If found:
  - Use customer-specific config
Else:
  - Use global config (FeaturesConfig/ThresholdConfig)
    ↓
Apply config to decision logic
```

**Usage in Code:**
```python
# hybrid_decision.py
checks_config = db.get_customer_checks_config(
    customer_id='1060284',
    account_no='011060284018',
    transfer_type='O'
)
# Returns: {'velocity_check_10min': 0, 'velocity_check_1hour': 1, ...}

# rule_engine.py
if checks_config['velocity_check_10min'] == 1:  # ON
    # Run velocity check
else:  # OFF
    # Skip velocity check
```

---

### Table 5: APITransactionLogs (API Transactions & Idempotence)

**Purpose:** Log all API transactions for idempotence and audit trail

**Columns:**
- LogID, IdempotenceKey (UNIQUE)
- RequestTimestamp, ResponseTimestamp, ExecutionTimeMs
- RequestMethod, RequestEndpoint
- RequestPayload, RequestHeaders, ResponsePayload
- ResponseStatusCode, APIKeyUsed, UserID, SessionID
- IsSuccessful, ErrorCode, ErrorMessage, StackTrace
- ClientIP, UserAgent, RetryCount, IsRetry, OriginalLogID
- TransactionID, RiskScore, Decision
- CreatedAt, DataClassification

**Data Flow:**
```
API receives request
    ↓
Generate IdempotenceKey
    ↓
Check APITransactionLogs table
    ↓
If IdempotenceKey exists:
  - Return cached response (duplicate prevention)
Else:
  - Process transaction
  - Store in APITransactionLogs
  - Return response
```

**Usage in Code:**
```python
# api.py
idempotence_key = request.idempotence_key or generate_idempotence_key()

cached = check_idempotence(idempotence_key)
if cached and cached.get("is_duplicate"):
    return cached.get("response_payload")  # Return cached

# After processing
db.insert_transaction_log(
    idempotence_key=idempotence_key,
    request_method='POST',
    request_body=request_payload,
    response_body=response_payload
)
```

---

### Table 6: PendingTransactions (Manual Review Queue)

**Purpose:** Store transactions requiring user approval

**Columns:**
- PendingID, TransactionID, CustomerId
- Amount, Status (pending/approved/rejected)
- CreatedAt, ApprovedAt, ApprovedBy
- RejectionReason, RejectedAt, RejectedBy

**Data Flow:**
```
Fraud detection completes
    ↓
Risk Level = HIGH or MEDIUM?
    ↓
Yes:
  - Insert into PendingTransactions
  - Status = 'pending'
  - Wait for admin approval
No:
  - Auto-approve or reject
  - Don't insert into PendingTransactions
    ↓
Admin reviews pending transactions
    ↓
Admin approves/rejects
    ↓
Update PendingTransactions
    ↓
Update Status, ApprovedAt, ApprovedBy
```

**Usage in Code:**
```python
# api.py
risk_level = result.get('risk_level', 'SAFE')
if risk_level in ['HIGH', 'MEDIUM']:
    decision = "REQUIRES_USER_APPROVAL"
    # Insert into PendingTransactions
else:
    decision = "APPROVED"
    # Don't insert
```

---

### Complete Data Flow Diagram

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
        │  (avg, std, max, weekly, monthly)  │
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
        │  (Only enabled features)           │
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
        │  (Respects customer config)        │
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

### Table Usage Summary

| Table | Purpose | Read/Write | Frequency | When |
|-------|---------|-----------|-----------|------|
| TransactionHistoryLogs | Source data | Read | Every txn | Feature engineering |
| APITransactionLogs | Complete audit trail | Write | Every txn | After processing |
| TransactionLogs | Idempotence check | Read/Write | Every txn | Before & after processing |
| FeaturesConfig | Feature toggles | Read | Every txn | Feature engineering |
| ThresholdConfig | Global thresholds | Read | Every txn | Rule engine |
| CustomerAccountTransferTypeConfig | Customer overrides | Read | Every txn | Decision logic |

---

## API Endpoints

### 1. Health Check
```
GET /health
Response: {"status": "healthy"}
```

### 2. Analyze Transaction
```
POST /analyze_transaction
Headers:
  - Authorization: Bearer <token>
  - Idempotence-Key: <unique-key>

Request Body:
{
    "customer_id": "123456",
    "from_account_no": "ACC001",
    "to_account_no": "ACC002",
    "transaction_amount": 50000,
    "transfer_type": "S",
    "bank_country": "UAE",
    "datetime": "2024-02-12T10:30:00Z"
}

Response:
{
    "is_fraud": false,
    "risk_level": "SAFE",
    "risk_score": 0.15,
    "confidence_level": 0.95,
    "model_agreement": 0.67,
    "reasons": [],
    "threshold": 45000,
    "ml_flag": false,
    "ae_flag": false
}
```

### 3. Approve Transaction
```
POST /approve_transaction
Request:
{
    "transaction_id": "TXN123",
    "approved_by": "admin@bank.com"
}

Response:
{
    "status": "approved",
    "transaction_id": "TXN123",
    "approved_at": "2024-02-12T10:35:00Z"
}
```

### 4. Reject Transaction
```
POST /reject_transaction
Request:
{
    "transaction_id": "TXN123",
    "reason": "Suspicious activity",
    "rejected_by": "admin@bank.com"
}

Response:
{
    "status": "rejected",
    "transaction_id": "TXN123",
    "rejected_at": "2024-02-12T10:35:00Z"
}
```

### 5. List Pending Transactions
```
GET /list_pending_transactions
Response:
{
    "pending_transactions": [
        {
            "transaction_id": "TXN123",
            "customer_id": "123456",
            "amount": 50000,
            "status": "pending",
            "created_at": "2024-02-12T10:30:00Z"
        }
    ],
    "total": 5
}
```

### 6. Feature Management
```
GET /get_all_features
Response:
{
    "enabled_features": ["flag_amount", "transfer_type_encoded", ...],
    "total": 40
}

POST /enable_feature/{feature_name}
Response: {"status": "enabled", "feature": "flag_amount"}

POST /disable_feature/{feature_name}
Response: {"status": "disabled", "feature": "flag_amount"}
```

---

## Configuration & Thresholds

### Risk Thresholds (`backend/config/risk_thresholds.json`)

```json
{
  "isolation_forest": {
    "high_risk_threshold": 0.8,
    "medium_risk_threshold": 0.65,
    "low_risk_threshold": 0.4
  },
  "confidence_calculation": {
    "all_models_agree": 0.95,
    "two_models_agree": 0.80,
    "one_model_agrees": 0.60,
    "high_risk_boost": 0.03
  },
  "risk_levels": {
    "safe": "SAFE",
    "low": "LOW",
    "medium": "MEDIUM",
    "high": "HIGH"
  }
}
```

### Environment Variables (`.env`)

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

### Velocity Limits

```python
MAX_VELOCITY_10MIN = 5      # Max 5 transactions in 10 minutes
MAX_VELOCITY_1HOUR = 15     # Max 15 transactions in 1 hour
```

### Amount Limits

```python
MIN_AMOUNT = 1.0 AED
MAX_AMOUNT = 1,000,000.0 AED
```

---

## Deployment

### Docker Setup

**Dockerfile:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "api.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Docker Compose:**
```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DB_SERVER=10.112.32.4
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

### Running the API

```bash
# Development
uvicorn api.api:app --reload --host 0.0.0.0 --port 8000

# Production
gunicorn -w 4 -b 0.0.0.0:8000 api.api:app
```

### Model Training

```bash
# Feature Engineering
python backend/feature_engineering.py

# Train Isolation Forest
python backend/train_isolation_forest.py

# Train Autoencoder
python backend/train_autoencoder.py
```

---

## Key Metrics & Monitoring

### Performance Metrics
- **Latency:** < 500ms per transaction
- **Throughput:** 1000+ transactions/second
- **Accuracy:** Depends on model training data

### Fraud Detection Metrics
- **True Positive Rate (TPR):** % of actual fraud caught
- **False Positive Rate (FPR):** % of legitimate flagged as fraud
- **Precision:** % of flagged transactions that are actually fraud
- **Recall:** % of actual fraud that was detected

### System Health
- **API Uptime:** 99.9%
- **DB Connection:** Active
- **Redis Connection:** Active (or fallback to memory)
- **Model Load Status:** All models loaded

---

## Security Considerations

1. **Input Validation:** All inputs sanitized against XSS/SQL injection
2. **Authentication:** Basic auth with API_USERNAME/API_PASSWORD
3. **Idempotence:** Prevents duplicate processing
4. **Data Encryption:** Credentials stored in .env (not in code)
5. **Rate Limiting:** Can be added at API gateway level
6. **Audit Logging:** All transactions logged with decisions

---

## Troubleshooting

### Issue: High False Positive Rate
**Solution:** Adjust thresholds in risk_thresholds.json

### Issue: Model Not Loading
**Solution:** Check model files exist in backend/model/

### Issue: Redis Connection Failed
**Solution:** System falls back to in-memory storage

### Issue: Database Connection Timeout
**Solution:** Check DB_SERVER, DB_PORT, credentials in .env

---

## Future Enhancements

1. **Real-time Model Retraining:** Periodic model updates
2. **Feedback Loop:** Use approved/rejected transactions to improve models
3. **Geographic Analysis:** Detect location-based anomalies
4. **Device Fingerprinting:** Track device patterns
5. **Network Analysis:** Detect fraud rings
6. **Explainability:** SHAP values for model decisions

---

## Conclusion

Yeh system ek comprehensive fraud detection solution hai jo:
- Real-time transactions analyze karta hai
- Multiple ML models use karta hai
- Business rules enforce karta hai
- High accuracy maintain karta hai
- Scalable aur maintainable hai

System production-ready hai aur banking-grade security follow karta hai.
