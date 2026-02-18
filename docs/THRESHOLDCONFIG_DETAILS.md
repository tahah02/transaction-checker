# ThresholdConfig Table - Complete Details

**Status:** ✅ Documented

---

## What is ThresholdConfig?

`ThresholdConfig` table stores **all threshold values** used by the fraud detection system. It allows dynamic threshold management without code changes.

---

## Table Structure

```sql
CREATE TABLE ThresholdConfig (
    ThresholdID INT PRIMARY KEY IDENTITY(1,1),
    ThresholdName NVARCHAR(100) NOT NULL,
    ThresholdType NVARCHAR(50) NOT NULL,
    ThresholdValue DECIMAL(10,6) NOT NULL,
    MinValue DECIMAL(10,6),
    MaxValue DECIMAL(10,6),
    PreviousValue DECIMAL(10,6),
    Description NVARCHAR(500),
    IsActive BIT NOT NULL DEFAULT 1,
    EffectiveFrom DATETIME NOT NULL DEFAULT GETDATE(),
    EffectiveTo DATETIME,
    CreatedAt DATETIME NOT NULL DEFAULT GETDATE(),
    UpdatedAt DATETIME,
    CreatedBy NVARCHAR(100),
    UpdatedBy NVARCHAR(100),
    Rationale NVARCHAR(500),
    ImpactAnalysis NVARCHAR(1000),
    ApprovalStatus NVARCHAR(50),
    ApprovedBy NVARCHAR(100),
    CONSTRAINT UQ_ThresholdName_Type UNIQUE (ThresholdName, ThresholdType),
    CONSTRAINT CHK_ThresholdValue CHECK (ThresholdValue >= MinValue AND ThresholdValue <= MaxValue)
);
```

---

## Thresholds Stored (23 Total)

### **1. Isolation Forest Thresholds (3)**

| ThresholdName | ThresholdType | ThresholdValue | MinValue | MaxValue | Description |
|---|---|---|---|---|---|
| IF_Anomaly_High | isolation_forest | 0.800000 | 0.300000 | 0.800000 | High risk anomaly threshold |
| IF_Anomaly_Medium | isolation_forest | 0.650000 | 0.300000 | 0.800000 | Medium risk anomaly threshold |
| IF_Anomaly_Low | isolation_forest | 0.400000 | 0.300000 | 0.800000 | Low risk anomaly threshold |

**Used In:** `backend/hybrid_decision.py` - Risk level calculation

---

### **2. Autoencoder Thresholds (1)**

| ThresholdName | ThresholdType | ThresholdValue | MinValue | MaxValue | Description |
|---|---|---|---|---|---|
| AE_Reconstruction | autoencoder | 1.914000 | 1.500000 | 2.500000 | Reconstruction error threshold |

**Used In:** `backend/autoencoder.py` - Anomaly detection

---

### **3. Velocity Thresholds (2)**

| ThresholdName | ThresholdType | ThresholdValue | MinValue | MaxValue | Description |
|---|---|---|---|---|---|
| Velocity_10min | velocity | 5.000000 | 1.000000 | 10.000000 | Max transactions in 10 minutes |
| Velocity_1hour | velocity | 15.000000 | 5.000000 | 30.000000 | Max transactions in 1 hour |

**Used In:** `backend/rule_engine.py` - Velocity checking

---

### **4. Amount Thresholds (7)**

Per transfer type multipliers and floors:

| ThresholdName | ThresholdType | ThresholdValue | MinValue | MaxValue | Description |
|---|---|---|---|---|---|
| Amount_Multiplier_S | amount | 2.000000 | 1.000000 | 5.000000 | Overseas multiplier |
| Amount_Multiplier_Q | amount | 2.500000 | 1.000000 | 5.000000 | Quick multiplier |
| Amount_Multiplier_L | amount | 3.000000 | 1.000000 | 5.000000 | UAE multiplier |
| Amount_Multiplier_I | amount | 3.500000 | 1.000000 | 5.000000 | Ajman multiplier |
| Amount_Multiplier_O | amount | 4.000000 | 1.000000 | 5.000000 | Own multiplier |
| Amount_Multiplier_M | amount | 3.200000 | 1.000000 | 5.000000 | MobilePay multiplier |
| Amount_Multiplier_F | amount | 3.800000 | 1.000000 | 5.000000 | Family Transfer multiplier |

**Formula:** `Monthly Limit = MAX(user_avg + multiplier × user_std, floor)`

**Used In:** `backend/rule_engine.py` - Monthly spending calculation

---

### **5. Amount Floor Thresholds (7)**

Minimum thresholds per transfer type:

| ThresholdName | ThresholdType | ThresholdValue | MinValue | MaxValue | Description |
|---|---|---|---|---|---|
| Amount_Floor_S | amount | 5000.000000 | 1000.000000 | 10000.000000 | Overseas floor |
| Amount_Floor_Q | amount | 3000.000000 | 1000.000000 | 10000.000000 | Quick floor |
| Amount_Floor_L | amount | 2000.000000 | 1000.000000 | 10000.000000 | UAE floor |
| Amount_Floor_I | amount | 1500.000000 | 1000.000000 | 10000.000000 | Ajman floor |
| Amount_Floor_O | amount | 1000.000000 | 1000.000000 | 10000.000000 | Own floor |
| Amount_Floor_M | amount | 1800.000000 | 1000.000000 | 10000.000000 | MobilePay floor |
| Amount_Floor_F | amount | 1200.000000 | 1000.000000 | 10000.000000 | Family Transfer floor |

**Used In:** `backend/rule_engine.py` - Monthly spending calculation

---

### **6. Confidence Thresholds (3)**

| ThresholdName | ThresholdType | ThresholdValue | MinValue | MaxValue | Description |
|---|---|---|---|---|---|
| Confidence_AllAgree | rule | 0.950000 | 0.800000 | 1.000000 | All 3 models agree |
| Confidence_TwoAgree | rule | 0.800000 | 0.600000 | 1.000000 | 2 models agree |
| Confidence_OneAgrees | rule | 0.600000 | 0.400000 | 1.000000 | 1 model agrees |

**Used In:** `backend/hybrid_decision.py` - Confidence calculation

---

## Example Data (INSERT Statements)

```sql
-- Isolation Forest Thresholds
INSERT INTO ThresholdConfig (ThresholdName, ThresholdType, ThresholdValue, MinValue, MaxValue, Description, CreatedBy)
VALUES 
('IF_Anomaly_High', 'isolation_forest', 0.8, 0.3, 0.8, 'High risk anomaly threshold', 'SYSTEM'),
('IF_Anomaly_Medium', 'isolation_forest', 0.65, 0.3, 0.8, 'Medium risk anomaly threshold', 'SYSTEM'),
('IF_Anomaly_Low', 'isolation_forest', 0.4, 0.3, 0.8, 'Low risk anomaly threshold', 'SYSTEM');

-- Autoencoder Threshold
INSERT INTO ThresholdConfig (ThresholdName, ThresholdType, ThresholdValue, MinValue, MaxValue, Description, CreatedBy)
VALUES 
('AE_Reconstruction', 'autoencoder', 1.914, 1.5, 2.5, 'Reconstruction error threshold', 'SYSTEM');

-- Velocity Thresholds
INSERT INTO ThresholdConfig (ThresholdName, ThresholdType, ThresholdValue, MinValue, MaxValue, Description, CreatedBy)
VALUES 
('Velocity_10min', 'velocity', 5, 1, 10, 'Max transactions in 10 minutes', 'SYSTEM'),
('Velocity_1hour', 'velocity', 15, 5, 30, 'Max transactions in 1 hour', 'SYSTEM');

-- Amount Multipliers
INSERT INTO ThresholdConfig (ThresholdName, ThresholdType, ThresholdValue, MinValue, MaxValue, Description, CreatedBy)
VALUES 
('Amount_Multiplier_S', 'amount', 2.0, 1.0, 5.0, 'Overseas multiplier', 'SYSTEM'),
('Amount_Multiplier_Q', 'amount', 2.5, 1.0, 5.0, 'Quick multiplier', 'SYSTEM'),
('Amount_Multiplier_L', 'amount', 3.0, 1.0, 5.0, 'UAE multiplier', 'SYSTEM'),
('Amount_Multiplier_I', 'amount', 3.5, 1.0, 5.0, 'Ajman multiplier', 'SYSTEM'),
('Amount_Multiplier_O', 'amount', 4.0, 1.0, 5.0, 'Own multiplier', 'SYSTEM'),
('Amount_Multiplier_M', 'amount', 3.2, 1.0, 5.0, 'MobilePay multiplier', 'SYSTEM'),
('Amount_Multiplier_F', 'amount', 3.8, 1.0, 5.0, 'Family Transfer multiplier', 'SYSTEM');

-- Amount Floors
INSERT INTO ThresholdConfig (ThresholdName, ThresholdType, ThresholdValue, MinValue, MaxValue, Description, CreatedBy)
VALUES 
('Amount_Floor_S', 'amount', 5000, 1000, 10000, 'Overseas floor', 'SYSTEM'),
('Amount_Floor_Q', 'amount', 3000, 1000, 10000, 'Quick floor', 'SYSTEM'),
('Amount_Floor_L', 'amount', 2000, 1000, 10000, 'UAE floor', 'SYSTEM'),
('Amount_Floor_I', 'amount', 1500, 1000, 10000, 'Ajman floor', 'SYSTEM'),
('Amount_Floor_O', 'amount', 1000, 1000, 10000, 'Own floor', 'SYSTEM'),
('Amount_Floor_M', 'amount', 1800, 1000, 10000, 'MobilePay floor', 'SYSTEM'),
('Amount_Floor_F', 'amount', 1200, 1000, 10000, 'Family Transfer floor', 'SYSTEM');

-- Confidence Thresholds
INSERT INTO ThresholdConfig (ThresholdName, ThresholdType, ThresholdValue, MinValue, MaxValue, Description, CreatedBy)
VALUES 
('Confidence_AllAgree', 'rule', 0.95, 0.8, 1.0, 'All 3 models agree', 'SYSTEM'),
('Confidence_TwoAgree', 'rule', 0.8, 0.6, 1.0, '2 models agree', 'SYSTEM'),
('Confidence_OneAgrees', 'rule', 0.6, 0.4, 1.0, '1 model agrees', 'SYSTEM');
```

---

## How to Modify Thresholds

### **Update a Threshold**
```sql
UPDATE ThresholdConfig 
SET ThresholdValue = 0.75,
    UpdatedAt = GETDATE(),
    UpdatedBy = 'ADMIN',
    Rationale = 'Adjusted for higher sensitivity'
WHERE ThresholdName = 'IF_Anomaly_High'
```

### **Add a New Threshold**
```sql
INSERT INTO ThresholdConfig (ThresholdName, ThresholdType, ThresholdValue, MinValue, MaxValue, Description, CreatedBy)
VALUES ('New_Threshold', 'rule', 0.5, 0.0, 1.0, 'New threshold description', 'ADMIN')
```

### **Disable a Threshold**
```sql
UPDATE ThresholdConfig 
SET IsActive = 0
WHERE ThresholdName = 'Velocity_10min'
```

---

## Threshold Types

| Type | Count | Purpose |
|---|---|---|
| `isolation_forest` | 3 | Anomaly detection thresholds |
| `autoencoder` | 1 | Reconstruction error threshold |
| `velocity` | 2 | Transaction velocity limits |
| `amount` | 14 | Amount multipliers and floors |
| `rule` | 3 | Confidence calculation thresholds |
| **TOTAL** | **23** | **All thresholds** |

---

## Key Features

✅ **Dynamic Management** - Change thresholds without code restart  
✅ **Audit Trail** - Track who changed what and when  
✅ **Rollback Support** - PreviousValue stored for easy rollback  
✅ **Validation** - MinValue/MaxValue constraints  
✅ **Approval Workflow** - ApprovalStatus for governance  
✅ **Effective Dates** - EffectiveFrom/EffectiveTo for scheduling  
✅ **Impact Analysis** - Document reason for changes  

---

## Status

**Total Thresholds:** 23  
**Table Status:** ✅ Created and Documented  
**Used In:** Multiple components (rule_engine, hybrid_decision, autoencoder)  
**Last Updated:** February 18, 2026
