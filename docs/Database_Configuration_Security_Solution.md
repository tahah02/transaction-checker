# Database Configuration & Security Solution Document

**Project:** Fraud Detection System  
**Database:** MSSQL  
**API Framework:** FastAPI  
**Date:** February 2026

---

## 1. Executive Summary

Ye document define karta hai:
- 5 MSSQL database tables ka schema
- Configuration management strategy (file + database)
- Secure API authentication (API Key + Basic Auth)
- Views for data accessibility
- Implementation timeline

---

## 2. Database Schema & Tables

### 2.1 Features Config Table
```sql
CREATE TABLE FeaturesConfig (
    FeatureID INT PRIMARY KEY IDENTITY(1,1),
    FeatureName NVARCHAR(100) NOT NULL UNIQUE,
    Description NVARCHAR(500),
    IsEnabled BIT NOT NULL DEFAULT 1,
    CreatedAt DATETIME DEFAULT GETDATE(),
    UpdatedAt DATETIME DEFAULT GETDATE(),
    CreatedBy NVARCHAR(100),
    UpdatedBy NVARCHAR(100)
);
```

**Purpose:** Feature flags management - enable/disable features without code deployment

---

### 2.2 Model Version Config Table
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
    CreatedAt DATETIME DEFAULT GETDATE(),
    DeployedAt DATETIME,
    CreatedBy NVARCHAR(100),
    UNIQUE(ModelName, VersionNumber)
);
```

**Purpose:** Track multiple model versions, switch between them, maintain history

---

### 2.3 File Version Maintenance Table
```sql
CREATE TABLE FileVersionMaintenance (
    FileVersionID INT PRIMARY KEY IDENTITY(1,1),
    FileName NVARCHAR(255) NOT NULL,
    FileType NVARCHAR(50) NOT NULL, -- 'model', 'scaler', 'config', 'data'
    FilePath NVARCHAR(500) NOT NULL,
    FileHash NVARCHAR(256),
    FileSize BIGINT,
    VersionNumber INT NOT NULL,
    Status NVARCHAR(50) NOT NULL, -- 'active', 'archived', 'deprecated'
    CreatedAt DATETIME DEFAULT GETDATE(),
    LastModifiedAt DATETIME,
    CreatedBy NVARCHAR(100),
    Notes NVARCHAR(500)
);
```

**Purpose:** Maintain file versions, track changes, enable rollback capability

---

### 2.4 Threshold Config Table
```sql
CREATE TABLE ThresholdConfig (
    ThresholdID INT PRIMARY KEY IDENTITY(1,1),
    ThresholdName NVARCHAR(100) NOT NULL,
    ThresholdType NVARCHAR(50) NOT NULL, -- 'autoencoder', 'isolation_forest', 'velocity'
    ThresholdValue DECIMAL(10,6) NOT NULL,
    MinValue DECIMAL(10,6),
    MaxValue DECIMAL(10,6),
    Description NVARCHAR(500),
    IsActive BIT NOT NULL DEFAULT 1,
    CreatedAt DATETIME DEFAULT GETDATE(),
    UpdatedAt DATETIME DEFAULT GETDATE(),
    CreatedBy NVARCHAR(100),
    UpdatedBy NVARCHAR(100),
    UNIQUE(ThresholdName, ThresholdType)
);
```

**Purpose:** Centralized threshold management for all ML models

---

### 2.5 Transaction Logs Table
```sql
CREATE TABLE TransactionLogs (
    LogID BIGINT PRIMARY KEY IDENTITY(1,1),
    IdempotenceKey NVARCHAR(255) NOT NULL UNIQUE,
    RequestTimestamp DATETIME NOT NULL DEFAULT GETDATE(),
    ResponseTimestamp DATETIME,
    RequestMethod NVARCHAR(50) NOT NULL, -- 'POST', 'GET', etc.
    RequestEndpoint NVARCHAR(255) NOT NULL,
    RequestPayload NVARCHAR(MAX),
    ResponsePayload NVARCHAR(MAX),
    ResponseStatusCode INT,
    ExecutionTimeMs INT,
    APIKeyUsed NVARCHAR(100),
    UserID NVARCHAR(100),
    IsSuccessful BIT,
    ErrorMessage NVARCHAR(MAX),
    CreatedAt DATETIME DEFAULT GETDATE()
);

CREATE INDEX IDX_IdempotenceKey ON TransactionLogs(IdempotenceKey);
CREATE INDEX IDX_RequestTimestamp ON TransactionLogs(RequestTimestamp);
CREATE INDEX IDX_APIKeyUsed ON TransactionLogs(APIKeyUsed);
```

**Purpose:** Log all API requests/responses for audit, debugging, idempotence handling

---

## 3. Database Views

### 3.1 View: vw_ActiveFeatures
```sql
CREATE VIEW vw_ActiveFeatures AS
SELECT 
    FeatureID,
    FeatureName,
    Description,
    IsEnabled,
    CreatedAt,
    UpdatedAt
FROM FeaturesConfig
WHERE IsEnabled = 1;
```

### 3.2 View: vw_ActiveModels
```sql
CREATE VIEW vw_ActiveModels AS
SELECT 
    ModelVersionID,
    ModelName,
    VersionNumber,
    ModelPath,
    Accuracy,
    DeployedAt
FROM ModelVersionConfig
WHERE IsActive = 1;
```

### 3.3 View: vw_ActiveThresholds
```sql
CREATE VIEW vw_ActiveThresholds AS
SELECT 
    ThresholdID,
    ThresholdName,
    ThresholdType,
    ThresholdValue,
    MinValue,
    MaxValue
FROM ThresholdConfig
WHERE IsActive = 1;
```

### 3.4 View: vw_RecentTransactionLogs
```sql
CREATE VIEW vw_RecentTransactionLogs AS
SELECT 
    LogID,
    IdempotenceKey,
    RequestTimestamp,
    ResponseTimestamp,
    RequestEndpoint,
    ResponseStatusCode,
    ExecutionTimeMs,
    IsSuccessful
FROM TransactionLogs
WHERE RequestTimestamp >= DATEADD(DAY, -7, GETDATE())
ORDER BY RequestTimestamp DESC;
```

---

## 4. Configuration Management Strategy

### 4.1 File-Based Configuration (Minimum Config)
**Location:** `config/app_config.json`

```json
{
  "database": {
    "server": "localhost",
    "database": "FraudDetectionDB",
    "driver": "ODBC Driver 17 for SQL Server"
  },
  "api": {
    "host": "0.0.0.0",
    "port": 8000,
    "environment": "production"
  },
  "security": {
    "api_key_header": "X-API-Key",
    "basic_auth_enabled": true,
    "token_expiry_hours": 24
  },
  "logging": {
    "level": "INFO",
    "max_log_size_mb": 100
  }
}
```

### 4.2 Database-Based Configuration (Maximum Config)
- **FeaturesConfig** - Feature toggles
- **ModelVersionConfig** - Model selection
- **ThresholdConfig** - Dynamic thresholds
- **FileVersionMaintenance** - File tracking

**Advantage:** Runtime changes without restart

---

## 5. Security Implementation

### 5.1 API Key Authentication
```
Header: X-API-Key: your-api-key-here
```

**Storage:** Hashed in database (bcrypt)

### 5.2 Basic Authentication
```
Header: Authorization: Basic base64(username:password)
```

### 5.3 Secure API Endpoints

**Protected Endpoints:**
- `POST /api/analyze` - Requires API Key
- `POST /api/approve` - Requires API Key + Basic Auth
- `POST /api/reject` - Requires API Key + Basic Auth
- `GET /api/config/*` - Requires API Key
- `PUT /api/config/*` - Requires API Key + Basic Auth

**Public Endpoints:**
- `GET /health` - No auth required

---

## 6. Implementation Timeline

| Phase | Task | Duration | Total |
|-------|------|----------|-------|
| **Phase 1** | Database schema creation (5 tables) | 30 min | 30 min |
| **Phase 2** | Create views (4 views) | 20 min | 50 min |
| **Phase 3** | API Key + Basic Auth middleware | 45 min | 1h 35m |
| **Phase 4** | Config file setup + DB connection | 30 min | 2h 05m |
| **Phase 5** | Transaction logging middleware | 40 min | 2h 45m |
| **Phase 6** | Testing + documentation | 45 min | 3h 30m |

**Total Estimated Time:** 3.5 hours (conservative estimate)

---

## 7. Implementation Steps

### Step 1: Database Setup
- Execute SQL scripts for all 5 tables
- Create all 4 views
- Add indexes for performance

### Step 2: Configuration
- Create `config/app_config.json`
- Update connection strings
- Set environment variables

### Step 3: Security Middleware
- Implement API Key validation
- Implement Basic Auth validation
- Add request/response logging

### Step 4: API Updates
- Add auth decorators to endpoints
- Implement idempotence checking
- Add transaction logging

### Step 5: Testing
- Test all endpoints with auth
- Verify logging
- Test idempotence

---

## 8. Database Connection (FastAPI)

```python
# config/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "mssql+pyodbc://user:password@server/database?driver=ODBC+Driver+17+for+SQL+Server"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## 9. API Key Management

**Create API Key:**
```sql
CREATE TABLE APIKeys (
    KeyID INT PRIMARY KEY IDENTITY(1,1),
    KeyHash NVARCHAR(255) NOT NULL UNIQUE,
    KeyName NVARCHAR(100),
    IsActive BIT DEFAULT 1,
    CreatedAt DATETIME DEFAULT GETDATE(),
    LastUsedAt DATETIME,
    ExpiresAt DATETIME
);
```

---

## 10. Next Steps

1. ✅ Approve this design
2. Create MSSQL database and tables
3. Implement FastAPI security middleware
4. Add transaction logging
5. Deploy and test

---

**Document Version:** 1.0  
**Last Updated:** February 10, 2026  
**Status:** Ready for Implementation
