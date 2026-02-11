# Implementation Guide - Part 1: Database & Configuration Setup

**Date:** February 2026  
**Status:** Step-by-Step Implementation  

---

## Phase 1: Database Setup (30 minutes)

### Step 1.1: Create MSSQL Database

```sql
-- Create database
CREATE DATABASE FraudDetectionDB;

-- Use database
USE FraudDetectionDB;

-- Set compatibility level
ALTER DATABASE FraudDetectionDB SET COMPATIBILITY_LEVEL = 150;
```

### Step 1.2: Create All 5 Tables

Execute the SQL scripts from `DATABASE_TABLES_DETAILED_SCHEMA.md`:

```sql
-- Table 1: FeaturesConfig
CREATE TABLE FeaturesConfig (
    FeatureID INT PRIMARY KEY IDENTITY(1,1),
    FeatureName NVARCHAR(100) NOT NULL UNIQUE,
    Description NVARCHAR(500),
    IsEnabled BIT NOT NULL DEFAULT 1,
    FeatureType NVARCHAR(50),
    Version NVARCHAR(50),
    CreatedAt DATETIME NOT NULL DEFAULT GETDATE(),
    UpdatedAt DATETIME,
    CreatedBy NVARCHAR(100),
    UpdatedBy NVARCHAR(100),
    RollbackVersion NVARCHAR(50),
    IsActive BIT NOT NULL DEFAULT 1
);

-- Table 2: ModelVersionConfig
CREATE TABLE ModelVersionConfig (
    ModelVersionID INT PRIMARY KEY IDENTITY(1,1),
    ModelName NVARCHAR(100) NOT NULL,
    VersionNumber NVARCHAR(50) NOT NULL,
    ModelPath NVARCHAR(500) NOT NULL,
    ScalerPath NVARCHAR(500),
    ThresholdPath NVARCHAR(500),
    IsActive BIT NOT NULL DEFAULT 0,
    Accuracy DECIMAL(5,4),
    Precision DECIMAL(5,4),
    Recall DECIMAL(5,4),
    F1Score DECIMAL(5,4),
    CreatedAt DATETIME NOT NULL DEFAULT GETDATE(),
    DeployedAt DATETIME,
    RetiredAt DATETIME,
    CreatedBy NVARCHAR(100),
    DeployedBy NVARCHAR(100),
    TrainingDataSize INT,
    ModelSize BIGINT,
    Notes NVARCHAR(500),
    CONSTRAINT UQ_ModelName_Version UNIQUE (ModelName, VersionNumber)
);

-- Table 3: FileVersionMaintenance
CREATE TABLE FileVersionMaintenance (
    FileVersionID INT PRIMARY KEY IDENTITY(1,1),
    FileName NVARCHAR(255) NOT NULL,
    FileType NVARCHAR(50) NOT NULL,
    FilePath NVARCHAR(500) NOT NULL,
    FileHash NVARCHAR(256) UNIQUE,
    FileSize BIGINT,
    VersionNumber INT NOT NULL DEFAULT 1,
    Status NVARCHAR(50) NOT NULL DEFAULT 'active',
    CreatedAt DATETIME NOT NULL DEFAULT GETDATE(),
    LastModifiedAt DATETIME,
    CreatedBy NVARCHAR(100),
    ModifiedBy NVARCHAR(100),
    PreviousVersionID INT,
    BackupPath NVARCHAR(500),
    ChecksumValidation BIT NOT NULL DEFAULT 0,
    Notes NVARCHAR(500),
    IsCompressed BIT NOT NULL DEFAULT 0,
    CompressionRatio DECIMAL(5,2),
    FOREIGN KEY (PreviousVersionID) REFERENCES FileVersionMaintenance(FileVersionID)
);

-- Table 4: ThresholdConfig
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

-- Table 5: TransactionLogs
CREATE TABLE TransactionLogs (
    LogID BIGINT PRIMARY KEY IDENTITY(1,1),
    IdempotenceKey NVARCHAR(255) NOT NULL UNIQUE,
    RequestTimestamp DATETIME NOT NULL DEFAULT GETDATE(),
    ResponseTimestamp DATETIME,
    ExecutionTimeMs INT,
    RequestMethod NVARCHAR(50) NOT NULL,
    RequestEndpoint NVARCHAR(255) NOT NULL,
    RequestPayload NVARCHAR(MAX),
    RequestHeaders NVARCHAR(MAX),
    ResponsePayload NVARCHAR(MAX),
    ResponseStatusCode INT,
    APIKeyUsed NVARCHAR(100),
    UserID NVARCHAR(100),
    SessionID NVARCHAR(255),
    IsSuccessful BIT,
    ErrorCode NVARCHAR(50),
    ErrorMessage NVARCHAR(MAX),
    StackTrace NVARCHAR(MAX),
    ClientIP NVARCHAR(50),
    UserAgent NVARCHAR(500),
    RetryCount INT NOT NULL DEFAULT 0,
    IsRetry BIT NOT NULL DEFAULT 0,
    OriginalLogID BIGINT,
    TransactionID NVARCHAR(100),
    RiskScore DECIMAL(5,4),
    Decision NVARCHAR(50),
    CreatedAt DATETIME NOT NULL DEFAULT GETDATE(),
    DataClassification NVARCHAR(50),
    FOREIGN KEY (OriginalLogID) REFERENCES TransactionLogs(LogID)
);
```

### Step 1.3: Create Indexes

```sql
-- FeaturesConfig Indexes
CREATE INDEX IDX_FeatureName ON FeaturesConfig(FeatureName);
CREATE INDEX IDX_IsEnabled ON FeaturesConfig(IsEnabled);
CREATE INDEX IDX_CreatedAt ON FeaturesConfig(CreatedAt);

-- ModelVersionConfig Indexes
CREATE INDEX IDX_ModelName ON ModelVersionConfig(ModelName);
CREATE INDEX IDX_IsActive ON ModelVersionConfig(IsActive);
CREATE INDEX IDX_CreatedAt ON ModelVersionConfig(CreatedAt);
CREATE INDEX IDX_DeployedAt ON ModelVersionConfig(DeployedAt);

-- FileVersionMaintenance Indexes
CREATE INDEX IDX_FileName ON FileVersionMaintenance(FileName);
CREATE INDEX IDX_FileType ON FileVersionMaintenance(FileType);
CREATE INDEX IDX_Status ON FileVersionMaintenance(Status);
CREATE INDEX IDX_CreatedAt ON FileVersionMaintenance(CreatedAt);
CREATE INDEX IDX_FileHash ON FileVersionMaintenance(FileHash);

-- ThresholdConfig Indexes
CREATE INDEX IDX_ThresholdName ON ThresholdConfig(ThresholdName);
CREATE INDEX IDX_ThresholdType ON ThresholdConfig(ThresholdType);
CREATE INDEX IDX_IsActive ON ThresholdConfig(IsActive);
CREATE INDEX IDX_EffectiveFrom ON ThresholdConfig(EffectiveFrom);

-- TransactionLogs Indexes
CREATE INDEX IDX_IdempotenceKey ON TransactionLogs(IdempotenceKey);
CREATE INDEX IDX_RequestTimestamp ON TransactionLogs(RequestTimestamp);
CREATE INDEX IDX_ResponseTimestamp ON TransactionLogs(ResponseTimestamp);
CREATE INDEX IDX_APIKeyUsed ON TransactionLogs(APIKeyUsed);
CREATE INDEX IDX_UserID ON TransactionLogs(UserID);
CREATE INDEX IDX_SessionID ON TransactionLogs(SessionID);
CREATE INDEX IDX_IsSuccessful ON TransactionLogs(IsSuccessful);
CREATE INDEX IDX_TransactionID ON TransactionLogs(TransactionID);
CREATE INDEX IDX_Decision ON TransactionLogs(Decision);
CREATE INDEX IDX_ClientIP ON TransactionLogs(ClientIP);
CREATE INDEX IDX_CreatedAt ON TransactionLogs(CreatedAt);

-- Composite Indexes
CREATE INDEX IDX_UserID_RequestTimestamp ON TransactionLogs(UserID, RequestTimestamp);
CREATE INDEX IDX_RequestEndpoint_RequestTimestamp ON TransactionLogs(RequestEndpoint, RequestTimestamp);
```

### Step 1.4: Create Views

```sql
-- View 1: Active Features
CREATE VIEW vw_ActiveFeatures AS
SELECT 
    FeatureID,
    FeatureName,
    Description,
    IsEnabled,
    FeatureType,
    Version,
    CreatedAt,
    UpdatedAt
FROM FeaturesConfig
WHERE IsEnabled = 1 AND IsActive = 1;

-- View 2: Active Models
CREATE VIEW vw_ActiveModels AS
SELECT 
    ModelVersionID,
    ModelName,
    VersionNumber,
    ModelPath,
    ScalerPath,
    Accuracy,
    Precision,
    Recall,
    F1Score,
    DeployedAt,
    CreatedBy
FROM ModelVersionConfig
WHERE IsActive = 1;

-- View 3: Active Thresholds
CREATE VIEW vw_ActiveThresholds AS
SELECT 
    ThresholdID,
    ThresholdName,
    ThresholdType,
    ThresholdValue,
    MinValue,
    MaxValue,
    Description,
    EffectiveFrom,
    EffectiveTo
FROM ThresholdConfig
WHERE IsActive = 1 
  AND EffectiveFrom <= GETDATE()
  AND (EffectiveTo IS NULL OR EffectiveTo >= GETDATE());

-- View 4: Recent Transaction Logs
CREATE VIEW vw_RecentTransactionLogs AS
SELECT 
    LogID,
    IdempotenceKey,
    RequestTimestamp,
    ResponseTimestamp,
    ExecutionTimeMs,
    RequestEndpoint,
    ResponseStatusCode,
    IsSuccessful,
    UserID,
    Decision,
    RiskScore
FROM TransactionLogs
WHERE RequestTimestamp >= DATEADD(DAY, -7, GETDATE())
ORDER BY RequestTimestamp DESC;

-- View 5: Failed Transactions
CREATE VIEW vw_FailedTransactions AS
SELECT 
    LogID,
    IdempotenceKey,
    RequestTimestamp,
    RequestEndpoint,
    ResponseStatusCode,
    ErrorCode,
    ErrorMessage,
    UserID,
    ClientIP
FROM TransactionLogs
WHERE IsSuccessful = 0
  AND RequestTimestamp >= DATEADD(DAY, -30, GETDATE())
ORDER BY RequestTimestamp DESC;
```

### Step 1.5: Insert Initial Data

```sql
-- Insert Features
INSERT INTO FeaturesConfig (FeatureName, Description, IsEnabled, FeatureType, Version, CreatedBy)
VALUES 
    ('IsolationForest', 'ML-based anomaly detection', 1, 'Detection', '1.0', 'admin'),
    ('Autoencoder', 'Deep learning behavioral analysis', 1, 'Detection', '1.0', 'admin'),
    ('RuleEngine', 'Business rule enforcement', 1, 'Detection', '1.0', 'admin'),
    ('TransactionLogging', 'API request/response logging', 1, 'Logging', '1.0', 'admin'),
    ('VelocityCheck', 'Transaction velocity validation', 1, 'Validation', '1.0', 'admin');

-- Insert Model Versions
INSERT INTO ModelVersionConfig (ModelName, VersionNumber, ModelPath, ScalerPath, ThresholdPath, IsActive, Accuracy, Precision, Recall, F1Score, CreatedBy, DeployedAt, DeployedBy)
VALUES 
    ('IsolationForest', '1.0', 'backend/model/isolation_forest.pkl', 'backend/model/isolation_forest_scaler.pkl', NULL, 1, 0.8500, 0.8600, 0.8400, 0.8500, 'admin', GETDATE(), 'admin'),
    ('Autoencoder', '1.0', 'backend/model/autoencoder.h5', 'backend/model/autoencoder_scaler.pkl', 'backend/model/autoencoder_threshold.json', 1, 0.8700, 0.8800, 0.8600, 0.8700, 'admin', GETDATE(), 'admin');

-- Insert Thresholds
INSERT INTO ThresholdConfig (ThresholdName, ThresholdType, ThresholdValue, MinValue, MaxValue, Description, IsActive, CreatedBy)
VALUES 
    ('IF_Anomaly', 'isolation_forest', 0.500000, 0.300000, 0.800000, 'Isolation Forest anomaly threshold', 1, 'admin'),
    ('AE_Reconstruction', 'autoencoder', 1.914000, 1.500000, 2.500000, 'Autoencoder reconstruction error threshold', 1, 'admin'),
    ('Velocity_10min', 'velocity', 5.000000, 1.000000, 10.000000, 'Max transactions in 10 minutes', 1, 'admin'),
    ('Velocity_1hour', 'velocity', 15.000000, 5.000000, 30.000000, 'Max transactions in 1 hour', 1, 'admin'),
    ('Amount_Limit_O', 'amount', 50000.000000, 10000.000000, 100000.000000, 'Amount limit for own account transfers', 1, 'admin');
```

---

## Phase 2: Python Database Service (30 minutes)

### Step 2.1: Create Database Service Class

Create file: `backend/db_service.py`

```python
import pymssql
import json
from datetime import datetime
from typing import List, Dict, Optional

class DatabaseService:
    def __init__(self, server: str, database: str, user: str, password: str):
        self.server = server
        self.database = database
        self.user = user
        self.password = password
        self.connection = None
    
    def connect(self) -> bool:
        try:
            self.connection = pymssql.connect(
                server=self.server,
                user=self.user,
                password=self.password,
                database=self.database
            )
            return True
        except Exception as e:
            print(f"Database connection error: {e}")
            return False
    
    def disconnect(self):
        if self.connection:
            self.connection.close()
    
    def execute_query(self, query: str, params: List = None) -> List[Dict]:
        try:
            cursor = self.connection.cursor(as_dict=True)
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            print(f"Query execution error: {e}")
            return []
    
    def execute_non_query(self, query: str, params: List = None) -> bool:
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Non-query execution error: {e}")
            self.connection.rollback()
            return False
    
    # Feature Configuration Methods
    def get_enabled_features(self) -> List[Dict]:
        query = "SELECT * FROM vw_ActiveFeatures"
        return self.execute_query(query)
    
    def enable_feature(self, feature_name: str) -> bool:
        query = "UPDATE FeaturesConfig SET IsEnabled = 1, UpdatedAt = GETDATE() WHERE FeatureName = ?"
        return self.execute_non_query(query, [feature_name])
    
    def disable_feature(self, feature_name: str) -> bool:
        query = "UPDATE FeaturesConfig SET IsEnabled = 0, UpdatedAt = GETDATE() WHERE FeatureName = ?"
        return self.execute_non_query(query, [feature_name])
    
    # Model Version Methods
    def get_active_models(self) -> List[Dict]:
        query = "SELECT * FROM vw_ActiveModels"
        return self.execute_query(query)
    
    def get_model_by_name(self, model_name: str) -> Optional[Dict]:
        query = "SELECT * FROM ModelVersionConfig WHERE ModelName = ? AND IsActive = 1"
        results = self.execute_query(query, [model_name])
        return results[0] if results else None
    
    def register_model_version(self, model_name: str, version: str, model_path: str, 
                              scaler_path: str, accuracy: float, created_by: str) -> bool:
        query = """
        INSERT INTO ModelVersionConfig 
        (ModelName, VersionNumber, ModelPath, ScalerPath, IsActive, Accuracy, CreatedBy)
        VALUES (?, ?, ?, ?, 0, ?, ?)
        """
        return self.execute_non_query(query, [model_name, version, model_path, scaler_path, accuracy, created_by])
    
    def activate_model(self, model_version_id: int, deployed_by: str) -> bool:
        # Deactivate all other versions of same model
        query1 = """
        UPDATE ModelVersionConfig SET IsActive = 0 
        WHERE ModelName = (SELECT ModelName FROM ModelVersionConfig WHERE ModelVersionID = ?)
        """
        self.execute_non_query(query1, [model_version_id])
        
        # Activate this version
        query2 = """
        UPDATE ModelVersionConfig 
        SET IsActive = 1, DeployedAt = GETDATE(), DeployedBy = ?
        WHERE ModelVersionID = ?
        """
        return self.execute_non_query(query2, [deployed_by, model_version_id])
    
    # Threshold Methods
    def get_active_thresholds(self) -> List[Dict]:
        query = "SELECT * FROM vw_ActiveThresholds"
        return self.execute_query(query)
    
    def get_threshold(self, threshold_name: str, threshold_type: str) -> Optional[Dict]:
        query = """
        SELECT * FROM ThresholdConfig 
        WHERE ThresholdName = ? AND ThresholdType = ? AND IsActive = 1
        """
        results = self.execute_query(query, [threshold_name, threshold_type])
        return results[0] if results else None
    
    def update_threshold(self, threshold_id: int, new_value: float, updated_by: str, rationale: str) -> bool:
        # Store previous value
        query1 = """
        UPDATE ThresholdConfig 
        SET PreviousValue = ThresholdValue, ThresholdValue = ?, UpdatedAt = GETDATE(), UpdatedBy = ?, Rationale = ?
        WHERE ThresholdID = ?
        """
        return self.execute_non_query(query1, [new_value, updated_by, rationale, threshold_id])
    
    # Transaction Logging Methods
    def log_transaction(self, idempotence_key: str, request_method: str, endpoint: str,
                       request_payload: str, api_key: str, user_id: str, session_id: str,
                       client_ip: str) -> bool:
        query = """
        INSERT INTO TransactionLogs 
        (IdempotenceKey, RequestMethod, RequestEndpoint, RequestPayload, APIKeyUsed, UserID, SessionID, ClientIP)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        return self.execute_non_query(query, [idempotence_key, request_method, endpoint, request_payload, api_key, user_id, session_id, client_ip])
    
    def update_transaction_response(self, idempotence_key: str, response_payload: str, 
                                   status_code: int, execution_time_ms: int, is_successful: bool,
                                   decision: str = None, risk_score: float = None) -> bool:
        query = """
        UPDATE TransactionLogs 
        SET ResponsePayload = ?, ResponseStatusCode = ?, ExecutionTimeMs = ?, 
            IsSuccessful = ?, ResponseTimestamp = GETDATE(), Decision = ?, RiskScore = ?
        WHERE IdempotenceKey = ?
        """
        return self.execute_non_query(query, [response_payload, status_code, execution_time_ms, is_successful, decision, risk_score, idempotence_key])
    
    def get_transaction_log(self, idempotence_key: str) -> Optional[Dict]:
        query = "SELECT * FROM TransactionLogs WHERE IdempotenceKey = ?"
        results = self.execute_query(query, [idempotence_key])
        return results[0] if results else None
    
    def get_recent_transactions(self, user_id: str = None, limit: int = 100) -> List[Dict]:
        if user_id:
            query = "SELECT TOP (?) * FROM vw_RecentTransactionLogs WHERE UserID = ? ORDER BY RequestTimestamp DESC"
            return self.execute_query(query, [limit, user_id])
        else:
            query = "SELECT TOP (?) * FROM vw_RecentTransactionLogs ORDER BY RequestTimestamp DESC"
            return self.execute_query(query, [limit])

# Singleton instance
_db_service = None

def get_db_service() -> DatabaseService:
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService(
            server='localhost',
            database='FraudDetectionDB',
            user='sa',
            password='your_password'
        )
        _db_service.connect()
    return _db_service
```

---

**Document Version:** 1.0  
**Status:** Part 1 Complete - Database & Service Setup
