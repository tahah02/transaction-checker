# Database Tables - Detailed Column Specifications

**Database:** MSSQL Server  
**Date:** February 2026  

---

## Table 1: FeaturesConfig

**Purpose:** Feature flags management - enable/disable features without code deployment

### Column Specifications

| Column Name | Data Type | Size | Nullable | Default | Primary Key | Unique | Index | Description |
|-------------|-----------|------|----------|---------|-------------|--------|-------|-------------|
| FeatureID | INT | - | NO | IDENTITY(1,1) | YES | - | - | Unique feature identifier |
| FeatureName | NVARCHAR | 100 | NO | - | NO | YES | YES | Feature name (e.g., 'IsolationForest', 'Autoencoder') |
| Description | NVARCHAR | 500 | YES | NULL | NO | NO | NO | Feature description |
| IsEnabled | BIT | - | NO | 1 | NO | NO | YES | Feature status (1=enabled, 0=disabled) |
| FeatureType | NVARCHAR | 50 | YES | NULL | NO | NO | NO | Type: 'Detection', 'Logging', 'Validation', 'Reporting' |
| Version | NVARCHAR | 50 | YES | NULL | NO | NO | NO | Feature version (e.g., '1.0', '2.1') |
| CreatedAt | DATETIME | - | NO | GETDATE() | NO | NO | YES | Creation timestamp |
| UpdatedAt | DATETIME | YES | NULL | NO | NO | YES | Last modification timestamp |
| CreatedBy | NVARCHAR | 100 | YES | NULL | NO | NO | NO | User who created feature |
| UpdatedBy | NVARCHAR | 100 | YES | NULL | NO | NO | NO | User who last updated feature |
| RollbackVersion | NVARCHAR | 50 | YES | NULL | NO | NO | NO | Previous version for rollback |
| IsActive | BIT | - | NO | 1 | NO | NO | NO | Active status (different from IsEnabled) |

### SQL Script

```sql
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

CREATE INDEX IDX_FeatureName ON FeaturesConfig(FeatureName);
CREATE INDEX IDX_IsEnabled ON FeaturesConfig(IsEnabled);
CREATE INDEX IDX_CreatedAt ON FeaturesConfig(CreatedAt);
```

### Example Data

```
FeatureID | FeatureName | IsEnabled | FeatureType | Version | CreatedAt
1         | IsolationForest | 1 | Detection | 1.0 | 2026-02-10
2         | Autoencoder | 1 | Detection | 1.0 | 2026-02-10
3         | RuleEngine | 1 | Detection | 1.0 | 2026-02-10
4         | TransactionLogging | 1 | Logging | 1.0 | 2026-02-10
5         | VelocityCheck | 1 | Validation | 1.0 | 2026-02-10
```

---

## Table 2: ModelVersionConfig

**Purpose:** Track multiple model versions, switch between them, maintain history

### Column Specifications

| Column Name | Data Type | Size | Nullable | Default | Primary Key | Unique | Index | Description |
|-------------|-----------|------|----------|---------|-------------|--------|-------|-------------|
| ModelVersionID | INT | - | NO | IDENTITY(1,1) | YES | - | - | Unique model version identifier |
| ModelName | NVARCHAR | 100 | NO | - | NO | NO | YES | Model name (e.g., 'IsolationForest', 'Autoencoder') |
| VersionNumber | NVARCHAR | 50 | NO | - | NO | NO | YES | Version number (e.g., '1.0', '1.1', '2.0') |
| ModelPath | NVARCHAR | 500 | NO | - | NO | NO | NO | File path to model (e.g., 'backend/model/isolation_forest.pkl') |
| ScalerPath | NVARCHAR | 500 | YES | NULL | NO | NO | NO | Path to feature scaler file |
| ThresholdPath | NVARCHAR | 500 | YES | NULL | NO | NO | NO | Path to threshold configuration |
| IsActive | BIT | - | NO | 0 | NO | NO | YES | Currently active model (1=active, 0=inactive) |
| Accuracy | DECIMAL | 5,4 | YES | NULL | NO | NO | NO | Model accuracy (0.0000 to 1.0000) |
| Precision | DECIMAL | 5,4 | YES | NULL | NO | NO | NO | Model precision score |
| Recall | DECIMAL | 5,4 | YES | NULL | NO | NO | NO | Model recall score |
| F1Score | DECIMAL | 5,4 | YES | NULL | NO | NO | NO | F1 score |
| CreatedAt | DATETIME | - | NO | GETDATE() | NO | NO | YES | Creation timestamp |
| DeployedAt | DATETIME | - | YES | NULL | NO | NO | YES | Deployment timestamp |
| RetiredAt | DATETIME | - | YES | NULL | NO | NO | NO | Retirement timestamp |
| CreatedBy | NVARCHAR | 100 | YES | NULL | NO | NO | NO | User who created model |
| DeployedBy | NVARCHAR | 100 | YES | NULL | NO | NO | NO | User who deployed model |
| TrainingDataSize | INT | - | YES | NULL | NO | NO | NO | Number of records used for training |
| ModelSize | BIGINT | - | YES | NULL | NO | NO | NO | Model file size in bytes |
| Notes | NVARCHAR | 500 | YES | NULL | NO | NO | NO | Additional notes/comments |

### Constraints

```sql
ALTER TABLE ModelVersionConfig
ADD CONSTRAINT UQ_ModelName_Version UNIQUE (ModelName, VersionNumber);
```

### SQL Script

```sql
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

CREATE INDEX IDX_ModelName ON ModelVersionConfig(ModelName);
CREATE INDEX IDX_IsActive ON ModelVersionConfig(IsActive);
CREATE INDEX IDX_CreatedAt ON ModelVersionConfig(CreatedAt);
CREATE INDEX IDX_DeployedAt ON ModelVersionConfig(DeployedAt);
```

### Example Data

```
ModelVersionID | ModelName | VersionNumber | IsActive | Accuracy | DeployedAt
1 | IsolationForest | 1.0 | 1 | 0.8500 | 2026-02-10
2 | IsolationForest | 1.1 | 0 | 0.8600 | NULL
3 | Autoencoder | 1.0 | 1 | 0.8700 | 2026-02-10
4 | Autoencoder | 1.1 | 0 | 0.8800 | NULL
```

---

## Table 3: FileVersionMaintenance

**Purpose:** Maintain file versions, track changes, enable rollback capability

### Column Specifications

| Column Name | Data Type | Size | Nullable | Default | Primary Key | Unique | Index | Description |
|-------------|-----------|------|----------|---------|-------------|--------|-------|-------------|
| FileVersionID | INT | - | NO | IDENTITY(1,1) | YES | - | - | Unique file version identifier |
| FileName | NVARCHAR | 255 | NO | - | NO | NO | YES | File name (e.g., 'isolation_forest.pkl') |
| FileType | NVARCHAR | 50 | NO | - | NO | NO | YES | Type: 'model', 'scaler', 'config', 'data', 'threshold' |
| FilePath | NVARCHAR | 500 | NO | - | NO | NO | NO | Full file path |
| FileHash | NVARCHAR | 256 | YES | NULL | NO | YES | YES | SHA-256 hash for integrity verification |
| FileSize | BIGINT | - | YES | NULL | NO | NO | NO | File size in bytes |
| VersionNumber | INT | - | NO | 1 | NO | NO | YES | Version number (1, 2, 3, ...) |
| Status | NVARCHAR | 50 | NO | 'active' | NO | NO | YES | Status: 'active', 'archived', 'deprecated', 'backup' |
| CreatedAt | DATETIME | - | NO | GETDATE() | NO | NO | YES | Creation timestamp |
| LastModifiedAt | DATETIME | - | YES | NULL | NO | NO | YES | Last modification timestamp |
| CreatedBy | NVARCHAR | 100 | YES | NULL | NO | NO | NO | User who created file |
| ModifiedBy | NVARCHAR | 100 | YES | NULL | NO | NO | NO | User who last modified file |
| PreviousVersionID | INT | - | YES | NULL | NO | NO | NO | Reference to previous version |
| BackupPath | NVARCHAR | 500 | YES | NULL | NO | NO | NO | Path to backup copy |
| ChecksumValidation | BIT | - | NO | 0 | NO | NO | NO | Checksum validation status |
| Notes | NVARCHAR | 500 | YES | NULL | NO | NO | NO | Additional notes |
| IsCompressed | BIT | - | NO | 0 | NO | NO | NO | Whether file is compressed |
| CompressionRatio | DECIMAL | 5,2 | YES | NULL | NO | NO | NO | Compression ratio percentage |

### SQL Script

```sql
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

CREATE INDEX IDX_FileName ON FileVersionMaintenance(FileName);
CREATE INDEX IDX_FileType ON FileVersionMaintenance(FileType);
CREATE INDEX IDX_Status ON FileVersionMaintenance(Status);
CREATE INDEX IDX_CreatedAt ON FileVersionMaintenance(CreatedAt);
CREATE INDEX IDX_FileHash ON FileVersionMaintenance(FileHash);
```

### Example Data

```
FileVersionID | FileName | FileType | Status | VersionNumber | FileSize
1 | isolation_forest.pkl | model | active | 1 | 2048576
2 | isolation_forest.pkl | model | archived | 0 | 2048576
3 | autoencoder.h5 | model | active | 1 | 5242880
4 | isolation_forest_scaler.pkl | scaler | active | 1 | 1024
5 | autoencoder_threshold.json | threshold | active | 1 | 512
```

---

## Table 4: ThresholdConfig

**Purpose:** Centralized threshold management for all ML models

### Column Specifications

| Column Name | Data Type | Size | Nullable | Default | Primary Key | Unique | Index | Description |
|-------------|-----------|------|----------|---------|-------------|--------|-------|-------------|
| ThresholdID | INT | - | NO | IDENTITY(1,1) | YES | - | - | Unique threshold identifier |
| ThresholdName | NVARCHAR | 100 | NO | - | NO | NO | YES | Threshold name (e.g., 'IF_Anomaly', 'AE_Reconstruction') |
| ThresholdType | NVARCHAR | 50 | NO | - | NO | NO | YES | Type: 'autoencoder', 'isolation_forest', 'velocity', 'amount', 'rule' |
| ThresholdValue | DECIMAL | 10,6 | NO | - | NO | NO | NO | Current threshold value |
| MinValue | DECIMAL | 10,6 | YES | NULL | NO | NO | NO | Minimum allowed value |
| MaxValue | DECIMAL | 10,6 | YES | NULL | NO | NO | NO | Maximum allowed value |
| PreviousValue | DECIMAL | 10,6 | YES | NULL | NO | NO | NO | Previous threshold value (for rollback) |
| Description | NVARCHAR | 500 | YES | NULL | NO | NO | NO | Threshold description |
| IsActive | BIT | - | NO | 1 | NO | NO | YES | Active status (1=active, 0=inactive) |
| EffectiveFrom | DATETIME | - | NO | GETDATE() | NO | NO | YES | When threshold becomes effective |
| EffectiveTo | DATETIME | - | YES | NULL | NO | NO | NO | When threshold expires |
| CreatedAt | DATETIME | - | NO | GETDATE() | NO | NO | YES | Creation timestamp |
| UpdatedAt | DATETIME | - | YES | NULL | NO | NO | YES | Last update timestamp |
| CreatedBy | NVARCHAR | 100 | YES | NULL | NO | NO | NO | User who created threshold |
| UpdatedBy | NVARCHAR | 100 | YES | NULL | NO | NO | NO | User who last updated threshold |
| Rationale | NVARCHAR | 500 | YES | NULL | NO | NO | NO | Reason for threshold value |
| ImpactAnalysis | NVARCHAR | 1000 | YES | NULL | NO | NO | NO | Expected impact of threshold change |
| ApprovalStatus | NVARCHAR | 50 | YES | NULL | NO | NO | NO | Approval status: 'pending', 'approved', 'rejected' |
| ApprovedBy | NVARCHAR | 100 | YES | NULL | NO | NO | NO | User who approved threshold |

### Constraints

```sql
ALTER TABLE ThresholdConfig
ADD CONSTRAINT UQ_ThresholdName_Type UNIQUE (ThresholdName, ThresholdType);

ALTER TABLE ThresholdConfig
ADD CONSTRAINT CHK_ThresholdValue CHECK (ThresholdValue >= MinValue AND ThresholdValue <= MaxValue);
```

### SQL Script

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

CREATE INDEX IDX_ThresholdName ON ThresholdConfig(ThresholdName);
CREATE INDEX IDX_ThresholdType ON ThresholdConfig(ThresholdType);
CREATE INDEX IDX_IsActive ON ThresholdConfig(IsActive);
CREATE INDEX IDX_EffectiveFrom ON ThresholdConfig(EffectiveFrom);
```

### Example Data

```
ThresholdID | ThresholdName | ThresholdType | ThresholdValue | MinValue | MaxValue
1 | IF_Anomaly | isolation_forest | 0.500000 | 0.300000 | 0.800000
2 | AE_Reconstruction | autoencoder | 1.914000 | 1.500000 | 2.500000
3 | Velocity_10min | velocity | 5.000000 | 1.000000 | 10.000000
4 | Velocity_1hour | velocity | 15.000000 | 5.000000 | 30.000000
5 | Amount_Limit_O | amount | 50000.000000 | 10000.000000 | 100000.000000
```

---

## Table 5: TransactionLogs

**Purpose:** Log all API requests/responses for audit, debugging, idempotence handling

### Column Specifications

| Column Name | Data Type | Size | Nullable | Default | Primary Key | Unique | Index | Description |
|-------------|-----------|------|----------|---------|-------------|--------|-------|-------------|
| LogID | BIGINT | - | NO | IDENTITY(1,1) | YES | - | - | Unique log identifier |
| IdempotenceKey | NVARCHAR | 255 | NO | - | NO | YES | YES | Unique idempotence key for request deduplication |
| RequestTimestamp | DATETIME | - | NO | GETDATE() | NO | NO | YES | When request was received |
| ResponseTimestamp | DATETIME | - | YES | NULL | NO | NO | YES | When response was sent |
| ExecutionTimeMs | INT | - | YES | NULL | NO | NO | NO | Total execution time in milliseconds |
| RequestMethod | NVARCHAR | 50 | NO | - | NO | NO | YES | HTTP method (GET, POST, PUT, DELETE) |
| RequestEndpoint | NVARCHAR | 255 | NO | - | NO | NO | YES | API endpoint (e.g., '/api/analyze-transaction') |
| RequestPayload | NVARCHAR | MAX | YES | NULL | NO | NO | NO | Full request body (JSON) |
| RequestHeaders | NVARCHAR | MAX | YES | NULL | NO | NO | NO | Request headers (sanitized) |
| ResponsePayload | NVARCHAR | MAX | YES | NULL | NO | NO | NO | Full response body (JSON) |
| ResponseStatusCode | INT | - | YES | NULL | NO | NO | YES | HTTP status code (200, 400, 500, etc.) |
| APIKeyUsed | NVARCHAR | 100 | YES | NULL | NO | NO | YES | API key used (hashed/masked) |
| UserID | NVARCHAR | 100 | YES | NULL | NO | NO | YES | User/Customer ID |
| SessionID | NVARCHAR | 255 | YES | NULL | NO | NO | YES | Session identifier |
| IsSuccessful | BIT | - | YES | NULL | NO | NO | YES | Success status (1=success, 0=failure) |
| ErrorCode | NVARCHAR | 50 | YES | NULL | NO | NO | NO | Error code if failed |
| ErrorMessage | NVARCHAR | MAX | YES | NULL | NO | NO | NO | Error message if failed |
| StackTrace | NVARCHAR | MAX | YES | NULL | NO | NO | NO | Stack trace if error occurred |
| ClientIP | NVARCHAR | 50 | YES | NULL | NO | NO | YES | Client IP address |
| UserAgent | NVARCHAR | 500 | YES | NULL | NO | NO | NO | User agent string |
| RetryCount | INT | - | NO | 0 | NO | NO | NO | Number of retries |
| IsRetry | BIT | - | NO | 0 | NO | NO | YES | Whether this is a retry request |
| OriginalLogID | BIGINT | - | YES | NULL | NO | NO | NO | Reference to original request if retry |
| TransactionID | NVARCHAR | 100 | YES | NULL | NO | NO | YES | Business transaction ID |
| RiskScore | DECIMAL | 5,4 | YES | NULL | NO | NO | NO | Fraud risk score (if applicable) |
| Decision | NVARCHAR | 50 | YES | NULL | NO | NO | YES | Decision: 'APPROVED', 'FLAGGED', 'BLOCKED' |
| CreatedAt | DATETIME | - | NO | GETDATE() | NO | NO | YES | Log creation timestamp |
| DataClassification | NVARCHAR | 50 | YES | NULL | NO | NO | NO | Data sensitivity: 'public', 'internal', 'confidential' |

### Constraints

```sql
ALTER TABLE TransactionLogs
ADD CONSTRAINT FK_OriginalLogID FOREIGN KEY (OriginalLogID) 
REFERENCES TransactionLogs(LogID);
```

### SQL Script

```sql
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

-- Composite indexes for common queries
CREATE INDEX IDX_UserID_RequestTimestamp ON TransactionLogs(UserID, RequestTimestamp);
CREATE INDEX IDX_RequestEndpoint_RequestTimestamp ON TransactionLogs(RequestEndpoint, RequestTimestamp);
```

### Example Data

```
LogID | IdempotenceKey | RequestMethod | RequestEndpoint | ResponseStatusCode | IsSuccessful | Decision
1 | req_abc123def456 | POST | /api/analyze-transaction | 200 | 1 | APPROVED
2 | req_xyz789uvw012 | POST | /api/analyze-transaction | 200 | 1 | FLAGGED
3 | req_pqr345stu678 | POST | /api/transaction/approve | 200 | 1 | NULL
4 | req_mno901jkl234 | GET | /api/health | 200 | 1 | NULL
5 | req_ghi567fgh890 | POST | /api/analyze-transaction | 400 | 0 | NULL
```

---

## Summary Table Comparison

| Table | Purpose | Rows/Day | Retention | Key Index |
|-------|---------|----------|-----------|-----------|
| FeaturesConfig | Feature flags | 0-10 | Permanent | FeatureName |
| ModelVersionConfig | Model tracking | 0-5 | Permanent | ModelName, IsActive |
| FileVersionMaintenance | File versions | 0-20 | 1 year | FileName, Status |
| ThresholdConfig | Threshold management | 0-10 | Permanent | ThresholdName, ThresholdType |
| TransactionLogs | API logging | 10,000+ | 1-2 years | IdempotenceKey, RequestTimestamp |

---

## Database Views

### View 1: vw_ActiveFeatures

```sql
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
```

### View 2: vw_ActiveModels

```sql
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
```

### View 3: vw_ActiveThresholds

```sql
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
```

### View 4: vw_RecentTransactionLogs

```sql
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
```

### View 5: vw_FailedTransactions

```sql
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

---

## Indexing Strategy

### Primary Indexes (High Priority)
- FeaturesConfig: FeatureName (unique)
- ModelVersionConfig: ModelName, IsActive
- FileVersionMaintenance: FileName, FileHash
- ThresholdConfig: ThresholdName, ThresholdType
- TransactionLogs: IdempotenceKey (unique), RequestTimestamp

### Secondary Indexes (Medium Priority)
- FeaturesConfig: IsEnabled, CreatedAt
- ModelVersionConfig: CreatedAt, DeployedAt
- FileVersionMaintenance: Status, CreatedAt
- ThresholdConfig: IsActive, EffectiveFrom
- TransactionLogs: UserID, SessionID, Decision

### Composite Indexes (Performance)
- TransactionLogs: (UserID, RequestTimestamp)
- TransactionLogs: (RequestEndpoint, RequestTimestamp)
- TransactionLogs: (IsSuccessful, RequestTimestamp)

---

## Data Types Reference

| Data Type | Usage | Size | Example |
|-----------|-------|------|---------|
| INT | IDs, counts, small numbers | 4 bytes | FeatureID, VersionNumber |
| BIGINT | Large IDs, file sizes | 8 bytes | LogID, FileSize |
| NVARCHAR(n) | Text, names, paths | 2n bytes | FeatureName, FilePath |
| NVARCHAR(MAX) | Large text, JSON | Variable | RequestPayload, ResponsePayload |
| DECIMAL(p,s) | Precise decimals | Variable | ThresholdValue, Accuracy |
| BIT | Boolean flags | 1 byte | IsEnabled, IsActive |
| DATETIME | Timestamps | 8 bytes | CreatedAt, RequestTimestamp |

---

**Document Version:** 1.0  
**Last Updated:** February 10, 2026  
**Status:** Ready for Implementation
