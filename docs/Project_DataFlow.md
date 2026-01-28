# Banking Fraud Detection System - Complete Data Flow

## **System Data Flow Overview** The Banking Fraud Detection System processes transaction data through multiple stages, from raw input to final fraud decision. This document details every step of data transformation and processing.

## **High-Level Data Flow Architecture** ```
Raw Transaction → Feature Engineering → Triple Detection → Final Decision
       ↓                    ↓                ↓              ↓
   CSV Input         41 Features      Rule + ML + AE    Block/Approve
```

## **Detailed Data Flow Stages** ### **Stage 1: Data Input & Validation** #### **Input Sources** ```
 Transaction Input
  Streamlit Web Interface
    User authentication
    Account selection
    Transaction form input
    Real-time validation
  CSV File Upload
    Bulk transaction processing
    Historical data analysis
    Batch fraud detection
  API Integration (Future)
     Real-time banking systems
     Mobile app transactions
     ATM transaction feeds
```

#### **Raw Transaction Fields** ```python
# Core Transaction Data
{
    'CustomerId': '1000016',
    'TransferType': 'S',  # S=Overseas, I=Ajman, L=UAE, Q=Quick, O=Own
    'FromAccountNo': '11000016019',
    'ReceipentAccount': 'DE89370400440532013000',
    'Amount': 119,
    'Currency': 'EUR',
    'CreateDate': '07/05/2025 16:17',
    'ChannelId': 1,
    'BankCountry': 'Germany',
    # ... additional fields
}
```

### **Stage 2: Feature Engineering Pipeline** #### **Data Preprocessing** ```
 Raw Data Processing
  DateTime Parsing
    CreateDate → pandas datetime
    Extract hour, day_of_week
    Calculate is_weekend, is_night
    Handle timezone conversions
  Amount Normalization
    Convert to AED base currency
    Handle currency conversions
    Validate amount ranges
    Clean invalid values
  Categorical Encoding
     TransferType → encoded values
     ChannelId → channel_encoded
     BankCountry → geo features
     Risk score mappings
```

#### **41 Feature Generation Process** ##### **Basic Transaction Features (5 features)** ```python
# Direct transaction attributes
transaction_amount = AmountInAed
flag_amount = 1 if TransferType == 'S' else 0  # International flag
transfer_type_encoded = TRANSFER_TYPE_ENCODED[TransferType]
transfer_type_risk = TRANSFER_TYPE_RISK[TransferType]
channel_encoded = channel_mapping[ChannelId]
```

##### **Temporal Features (8 features)** ```python
# Time-based patterns
hour = CreateDate.hour  # 0-23
day_of_week = CreateDate.dayofweek  # 0-6
is_weekend = 1 if day_of_week >= 5 else 0
is_night = 1 if hour < 6 or hour >= 22 else 0
time_since_last = current_time - last_transaction_time
recent_burst = 1 if time_since_last < 300 else 0  # 5 minutes
transaction_velocity = 1 / (time_since_last / 3600)  # per hour
```

##### **User Behavioral Features (8 features)** ```python
# Historical user patterns
user_avg_amount = mean(user_historical_amounts)
user_std_amount = std(user_historical_amounts)
user_max_amount = max(user_historical_amounts)
user_txn_frequency = count(user_transactions)
deviation_from_avg = abs(current_amount - user_avg_amount)
amount_to_max_ratio = current_amount / user_max_amount
intl_ratio = count(international_txns) / total_txns
user_high_risk_txn_ratio = count(high_risk_txns) / total_txns
```

##### **Account & Beneficiary Features (6 features)** ```python
# Account usage patterns
num_accounts = unique_count(user_accounts)
user_multiple_accounts_flag = 1 if num_accounts > 1 else 0
cross_account_transfer_ratio = cross_account_txns / total_txns
geo_anomaly_flag = 1 if unique_countries > 2 else 0
is_new_beneficiary = 1 if beneficiary not in history else 0
beneficiary_txn_count_30d = count(beneficiary_txns_last_30d)
```

##### **Velocity & Frequency Features (6 features)** ```python
# Transaction velocity tracking
txn_count_30s = count(transactions_last_30_seconds)
txn_count_10min = count(transactions_last_10_minutes)
txn_count_1hour = count(transactions_last_1_hour)
hourly_total = sum(amounts_this_hour)
hourly_count = count(transactions_this_hour)
daily_total = sum(amounts_today)
daily_count = count(transactions_today)
```

##### **Advanced Analytics Features (8 features)** ```python
# Weekly patterns
weekly_total = sum(amounts_this_week)
weekly_txn_count = count(transactions_this_week)
weekly_avg_amount = mean(amounts_this_week)
weekly_deviation = abs(current_amount - weekly_avg_amount)
amount_vs_weekly_avg = current_amount / weekly_avg_amount

# Monthly patterns
current_month_spending = sum(amounts_this_month)
monthly_txn_count = count(transactions_this_month)
monthly_avg_amount = mean(amounts_this_month)
monthly_deviation = abs(current_amount - monthly_avg_amount)
amount_vs_monthly_avg = current_amount / monthly_avg_amount

# Statistical measures
rolling_std = std(last_5_transactions)
```

### **Stage 3: Triple Detection Pipeline** #### **Detection Layer 1: Rule Engine** ```
 Business Rules Processing
  Input: 41 engineered features
  Velocity Checks
    txn_count_30s ≤ 2
    txn_count_10min ≤ 5
    txn_count_1hour ≤ 15
    recent_burst validation
  Amount Limits
    transaction_amount ≤ user_limit
    daily_total ≤ daily_limit
    weekly_total ≤ weekly_limit
    monthly_total ≤ monthly_limit
  Transfer Type Rules
    Overseas (S): stricter limits
    UAE (L): standard limits
    Quick (Q): medium limits
    Own (O): relaxed limits
  Output: BLOCK/PASS + violation details
```

#### **Detection Layer 2: Isolation Forest** ```
 Statistical Anomaly Detection
  Input: 41 normalized features
  Processing Pipeline
    Feature validation (all 41 present)
    StandardScaler normalization
    Isolation Forest prediction
    Anomaly score calculation
  Decision Logic
    prediction = model.predict(features)
    anomaly_score = model.decision_function(features)
    is_anomaly = prediction == -1
    confidence = abs(anomaly_score)
  Output: anomaly_score, is_anomaly, confidence
```

#### **Detection Layer 3: Autoencoder** ```
 Behavioral Pattern Analysis
  Input: 41 normalized features
  Neural Network Processing
    Feature validation and scaling
    Forward pass through network
    Reconstruction error calculation
    Threshold comparison
  Network Architecture
    Input Layer: 41 features
    Encoder: [64, 32] → 14 (bottleneck)
    Decoder: 14 → [32, 64] → 41
    Reconstruction: MSE loss
  Anomaly Detection
    reconstruction_error = MSE(input, output)
    is_anomaly = error > threshold
    threshold = mean + 3*std (from training)
    confidence = error / threshold
  Output: reconstruction_error, is_anomaly, confidence
```

### **Stage 4: Decision Aggregation** #### **Hybrid Decision Logic** ```python
def make_final_decision(rule_result, if_result, ae_result):
    # Priority 1: Hard business rule violations
    if rule_result['blocked']:
        return {
            'decision': 'BLOCKED',
            'reason': rule_result['violation'],
            'confidence': 1.0,
            'primary_detector': 'Rule Engine'
        }
    
    # Priority 2: Statistical anomalies
    if if_result['is_anomaly']:
        return {
            'decision': 'FLAGGED',
            'reason': f"Statistical anomaly: {if_result['anomaly_score']:.4f}",
            'confidence': abs(if_result['anomaly_score']),
            'primary_detector': 'Isolation Forest'
        }
    
    # Priority 3: Behavioral anomalies
    if ae_result['is_anomaly']:
        return {
            'decision': 'FLAGGED',
            'reason': f"Behavioral anomaly: {ae_result['reconstruction_error']:.4f}",
            'confidence': ae_result['reconstruction_error'] / ae_result['threshold'],
            'primary_detector': 'Autoencoder'
        }
    
    # All clear
    return {
        'decision': 'APPROVED',
        'reason': 'All detection layers passed',
        'confidence': 0.95,
        'primary_detector': 'Combined System'
    }
```

### **Stage 5: Result Processing & Output** #### **Decision Output Structure** ```python
{
    # Final Decision
    'final_decision': 'BLOCKED/FLAGGED/APPROVED',
    'confidence_score': 0.85,
    'risk_level': 'HIGH/MEDIUM/LOW',
    
    # Individual Layer Results
    'rule_engine': {
        'blocked': False,
        'violations': [],
        'checks_passed': ['velocity', 'amount_limits']
    },
    'isolation_forest': {
        'is_anomaly': True,
        'anomaly_score': -0.15,
        'confidence': 0.75
    },
    'autoencoder': {
        'is_anomaly': False,
        'reconstruction_error': 0.023,
        'threshold': 0.045,
        'confidence': 0.51
    },
    
    # Feature Analysis
    'key_features': {
        'transaction_amount': 5000.0,
        'deviation_from_avg': 3500.0,
        'user_avg_amount': 1500.0,
        'txn_count_1hour': 3
    },
    
    # Recommendations
    'recommended_action': 'Manual Review Required',
    'review_priority': 'HIGH',
    'additional_checks': ['Verify beneficiary', 'Contact customer']
}
```

## **Data Flow Performance Metrics** ### **Processing Times** ```
⏱ Stage Performance
 Feature Engineering: ~10ms
 Rule Engine: ~2ms
 Isolation Forest: ~15ms
 Autoencoder: ~25ms
 Decision Aggregation: ~3ms
 Total Processing: ~55ms
```

### **Data Volumes** ```
 Data Throughput
 Features per Transaction: 41
 Transactions per Second: 1000+
 Daily Transaction Volume: 100,000+
 Feature Data Size: ~2KB per transaction
 Model Memory Usage: ~100MB total
```

## **Data Flow Monitoring** ### **Key Monitoring Points** ```
 Monitoring Dashboard
  Feature Quality Metrics
    Missing feature rates
    Feature distribution drift
    Outlier detection rates
    Data quality scores
  Model Performance
    Prediction latencies
    Anomaly detection rates
    False positive rates
    Model accuracy metrics
  System Health
    Processing throughput
    Error rates by stage
    Memory usage patterns
    Response time distributions
  Business Metrics
     Fraud detection rates
     Customer impact scores
     Cost savings metrics
     Compliance adherence
```

### **Data Quality Checks** ```python
# Automated Data Validation
def validate_data_flow():
    # Feature completeness
    assert all(feature in transaction for feature in MODEL_FEATURES)
    
    # Value ranges
    assert 0 <= transaction_amount <= MAX_AMOUNT
    assert 0 <= hour <= 23
    assert 0 <= day_of_week <= 6
    
    # Logical consistency
    assert weekly_total >= daily_total
    assert monthly_total >= weekly_total
    assert user_max_amount >= transaction_amount
    
    # Model input validation
    assert len(feature_vector) == 41
    assert not np.any(np.isnan(feature_vector))
    assert not np.any(np.isinf(feature_vector))
```

## **Data Flow Optimization** ### **Performance Optimizations** - **Feature Caching**: Cache user behavioral features for repeat customers
- **Batch Processing**: Process multiple transactions together when possible
- **Model Caching**: Keep models loaded in memory with @st.cache_resource
- **Parallel Processing**: Run Isolation Forest and Autoencoder in parallel

### **Scalability Considerations** - **Horizontal Scaling**: Stateless design allows multiple instances
- **Database Optimization**: Efficient queries for historical data
- **Memory Management**: Optimized feature storage and retrieval
- **Load Balancing**: Distribute processing across multiple servers

This comprehensive data flow ensures robust, scalable, and accurate fraud detection while maintaining high performance and reliability for real-time transaction processing.