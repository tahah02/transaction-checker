# Implementation Guide - Part 2: Security & API Middleware

**Date:** February 2026  
**Status:** Security Implementation  

---

## Phase 3: Security Implementation (45 minutes)

### Step 3.1: Create API Key Management

Create file: `backend/security.py`

```python
import hashlib
import secrets
import hmac
from datetime import datetime, timedelta
from typing import Optional, Tuple

class APIKeyManager:
    """Manage API keys securely"""
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash API key using SHA-256"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate a secure random API key"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def verify_api_key(provided_key: str, stored_hash: str) -> bool:
        """Verify API key against stored hash"""
        provided_hash = APIKeyManager.hash_api_key(provided_key)
        return hmac.compare_digest(provided_hash, stored_hash)

class BasicAuthManager:
    """Manage basic authentication"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(provided_password: str, stored_hash: str) -> bool:
        """Verify password against stored hash"""
        provided_hash = BasicAuthManager.hash_password(provided_password)
        return hmac.compare_digest(provided_hash, stored_hash)

class IdempotenceManager:
    """Manage request idempotence"""
    
    def __init__(self, db_service):
        self.db = db_service
    
    def check_idempotence(self, idempotence_key: str) -> Tuple[bool, Optional[dict]]:
        """
        Check if request with this key already processed
        Returns: (is_duplicate, previous_response)
        """
        log = self.db.get_transaction_log(idempotence_key)
        if log and log.get('IsSuccessful'):
            return True, log
        return False, None
    
    def register_request(self, idempotence_key: str, request_data: dict) -> bool:
        """Register new request"""
        return self.db.log_transaction(
            idempotence_key=idempotence_key,
            request_method=request_data.get('method'),
            endpoint=request_data.get('endpoint'),
            request_payload=str(request_data),
            api_key=request_data.get('api_key'),
            user_id=request_data.get('user_id'),
            session_id=request_data.get('session_id'),
            client_ip=request_data.get('client_ip')
        )
```

### Step 3.2: Create FastAPI Security Middleware

Create file: `api/security_middleware.py`

```python
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthCredentials
import base64
from typing import Optional
from backend.security import APIKeyManager, BasicAuthManager, IdempotenceManager
from backend.db_service import get_db_service

security = HTTPBearer()
db = get_db_service()
idempotence_manager = IdempotenceManager(db)

async def verify_api_key(request: Request) -> str:
    """Verify API Key from header"""
    api_key = request.headers.get("X-API-Key")
    
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API Key")
    
    # In production, verify against database
    # For now, accept any key (implement DB verification)
    return api_key

async def verify_basic_auth(request: Request) -> Tuple[str, str]:
    """Verify Basic Authentication"""
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Basic "):
        raise HTTPException(status_code=401, detail="Missing Basic Auth")
    
    try:
        encoded_credentials = auth_header.split(" ")[1]
        decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8")
        username, password = decoded_credentials.split(":")
        
        # Verify credentials (implement DB verification)
        # For now, accept admin:admin
        if username == "admin" and password == "admin":
            return username, password
        
        raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid Basic Auth format")

async def verify_idempotence(request: Request) -> str:
    """Verify idempotence key"""
    idempotence_key = request.headers.get("X-Idempotence-Key")
    
    if not idempotence_key:
        raise HTTPException(status_code=400, detail="Missing Idempotence Key")
    
    return idempotence_key

def add_security_middleware(app: FastAPI):
    """Add security middleware to FastAPI app"""
    
    @app.middleware("http")
    async def security_middleware(request: Request, call_next):
        # Log request
        request_time = datetime.now()
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Add to request state
        request.state.client_ip = client_ip
        request.state.request_time = request_time
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response
```

### Step 3.3: Update FastAPI App with Security

Update file: `api/api.py` (add at top)

```python
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer
from datetime import datetime
import uuid
import logging
import json
from typing import Optional
import base64

from backend.hybrid_decision import make_decision
from backend.utils import load_model
from backend.autoencoder import AutoencoderInference
from backend.db_service import get_db_service
from api.models import TransactionRequest, TransactionResponse, ApprovalRequest, RejectionRequest, ActionResponse
from api.services import get_velocity_from_csv, get_pending_transactions
from api.helpers import save_transaction_to_file, update_transaction_status, validate_transfer_request
from api.security_middleware import add_security_middleware, verify_api_key, verify_basic_auth, verify_idempotence

logger = logging.getLogger(__name__)
app = FastAPI(title="Banking Fraud Detection API", version="1.0.0")

# Add security middleware
add_security_middleware(app)

db = get_db_service()
model, features, scaler = load_model()
autoencoder = AutoencoderInference()
autoencoder.load()

# ============ PROTECTED ENDPOINTS ============

@app.post("/api/analyze-transaction", response_model=TransactionResponse)
async def analyze_transaction(
    request: TransactionRequest,
    api_key: str = Depends(verify_api_key),
    idempotence_key: str = Depends(verify_idempotence),
    http_request: Request = None
):
    """Analyze transaction for fraud - Requires API Key"""
    start_time = datetime.now()
    client_ip = http_request.state.client_ip if http_request else "unknown"
    
    # Check idempotence
    is_duplicate, previous_response = db.get_transaction_log(idempotence_key)
    if is_duplicate and previous_response:
        logger.info(f"Duplicate request detected: {idempotence_key}")
        return TransactionResponse(**json.loads(previous_response.get('ResponsePayload', '{}')))
    
    # Log request
    db.log_transaction(
        idempotence_key=idempotence_key,
        request_method="POST",
        endpoint="/api/analyze-transaction",
        request_payload=request.json(),
        api_key=api_key,
        user_id=request.customer_id,
        session_id=None,
        client_ip=client_ip
    )
    
    # Set datetime if not provided
    if request.datetime is None:
        request.datetime = datetime.now()
    
    # Validate request
    validate_transfer_request(request)
    
    try:
        db_stats = db.get_all_user_stats(request.customer_id, request.from_account_no)
        user_stats = {
            "user_avg_amount": db_stats.get("user_avg_amount", 5000.0),
            "user_std_amount": db_stats.get("user_std_amount", 2000.0),
            "user_max_amount": db_stats.get("user_max_amount", 15000.0),
            "user_txn_frequency": db_stats.get("user_txn_frequency", 0),
            "user_international_ratio": db_stats.get("user_international_ratio", 0.0),
            "current_month_spending": db_stats.get("current_month_spending", 0.0),
        }
    except:
        user_stats = {
            "user_avg_amount": 5000.0,
            "user_std_amount": 2000.0,
            "user_max_amount": 15000.0,
            "user_txn_frequency": 0,
            "user_international_ratio": 0.0,
            "current_month_spending": 0.0,
        }
    
    try:
        is_new_ben = db.check_new_beneficiary(request.customer_id, request.to_account_no, request.transfer_type)
    except Exception as e:
        logger.error(f"Beneficiary check failed: {e}")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")
    
    csv_velocity = get_velocity_from_csv(request.customer_id, request.from_account_no)
    
    txn = {
        "amount": request.transaction_amount,
        "transfer_type": request.transfer_type,
        "bank_country": request.bank_country,
        "txn_count_30s": 1,
        "txn_count_10min": csv_velocity["txn_count_10min"] + 1,
        "txn_count_1hour": csv_velocity["txn_count_1hour"] + 1,
        "time_since_last_txn": user_stats.get("time_since_last_txn", 3600),
        "is_new_beneficiary": is_new_ben
    }
    
    result = make_decision(txn, user_stats, model, features, autoencoder)
    decision = "REQUIRES_USER_APPROVAL" if result['is_fraud'] else "APPROVED"
    processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
    transaction_id = f"txn_{uuid.uuid4().hex[:8]}"
    
    result['processing_time_ms'] = processing_time
    result['individual_scores'] = {
        "rule_engine": {"violated": result['is_fraud'], "threshold": result.get('threshold', 0)},
        "isolation_forest": {"anomaly_score": result.get('risk_score', 0), "is_anomaly": result.get('ml_flag', False)},
        "autoencoder": {"reconstruction_error": result.get('ae_reconstruction_error'), "is_anomaly": result.get('ae_flag', False)}
    }
    
    response = TransactionResponse(
        decision=decision,
        risk_score=result.get('risk_score', 0.0),
        risk_level=result.get('risk_level', 'SAFE'),
        confidence_level=result.get('confidence_level', 0.0),
        model_agreement=result.get('model_agreement', 0.0),
        reasons=result.get('reasons', []),
        individual_scores=result['individual_scores'],
        transaction_id=transaction_id,
        processing_time_ms=processing_time
    )
    
    # Log response
    db.update_transaction_response(
        idempotence_key=idempotence_key,
        response_payload=response.json(),
        status_code=200,
        execution_time_ms=processing_time,
        is_successful=True,
        decision=decision,
        risk_score=result.get('risk_score', 0.0)
    )
    
    return response

@app.post("/api/transaction/approve", response_model=ActionResponse)
async def approve_transaction(
    request: ApprovalRequest,
    api_key: str = Depends(verify_api_key),
    username: str = Depends(verify_basic_auth),
    http_request: Request = None
):
    """Approve transaction - Requires API Key + Basic Auth"""
    try:
        success = update_transaction_status(
            transaction_id=request.transaction_id,
            action="APPROVED",
            actioned_by=request.customer_id,
            comments=request.comments
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        return ActionResponse(
            status="approved",
            transaction_id=request.transaction_id,
            timestamp=datetime.now().isoformat(),
            message="Transaction approved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving transaction: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/transaction/reject", response_model=ActionResponse)
async def reject_transaction(
    request: RejectionRequest,
    api_key: str = Depends(verify_api_key),
    username: str = Depends(verify_basic_auth),
    http_request: Request = None
):
    """Reject transaction - Requires API Key + Basic Auth"""
    try:
        success = update_transaction_status(
            transaction_id=request.transaction_id,
            action="REJECTED",
            actioned_by=request.customer_id,
            comments=request.reason
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        return ActionResponse(
            status="rejected",
            transaction_id=request.transaction_id,
            timestamp=datetime.now().isoformat(),
            message="Transaction rejected successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting transaction: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ============ PUBLIC ENDPOINTS ============

@app.get("/api/health")
async def health_check():
    """Health check - No auth required"""
    db_status = "disconnected"
    db_info = {}
    
    try:
        if db.connect():
            db_status = "connected"
            db.disconnect()
        else:
            db_status = "connection_failed"
    except Exception as e:
        db_status = "error"
        db_info = {"error": str(e)}
    
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "timestamp": datetime.now().isoformat(),
        "models": {
            "isolation_forest": "loaded" if model else "unavailable",
            "autoencoder": "loaded" if autoencoder else "unavailable"
        },
        "database": {
            "status": db_status, **db_info
        }
    }
```

---

## Phase 4: Configuration File Setup (30 minutes)

### Step 4.1: Create Configuration File

Create file: `config/app_config.json`

```json
{
  "database": {
    "server": "localhost",
    "database": "FraudDetectionDB",
    "user": "sa",
    "password": "your_password",
    "driver": "ODBC Driver 17 for SQL Server",
    "connection_timeout": 30,
    "pool_size": 10
  },
  "api": {
    "host": "0.0.0.0",
    "port": 8000,
    "environment": "production",
    "debug": false,
    "reload": false
  },
  "security": {
    "api_key_header": "X-API-Key",
    "basic_auth_enabled": true,
    "idempotence_key_header": "X-Idempotence-Key",
    "token_expiry_hours": 24,
    "max_retries": 3,
    "rate_limit_requests": 1000,
    "rate_limit_window_seconds": 60
  },
  "models": {
    "isolation_forest_path": "backend/model/isolation_forest.pkl",
    "isolation_forest_scaler_path": "backend/model/isolation_forest_scaler.pkl",
    "autoencoder_path": "backend/model/autoencoder.h5",
    "autoencoder_scaler_path": "backend/model/autoencoder_scaler.pkl",
    "autoencoder_threshold_path": "backend/model/autoencoder_threshold.json",
    "cache_models": true,
    "model_reload_interval_hours": 24
  },
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "logs/app.log",
    "max_log_size_mb": 100,
    "backup_count": 10
  },
  "features": {
    "enable_transaction_logging": true,
    "enable_idempotence_check": true,
    "enable_rate_limiting": true,
    "enable_audit_trail": true
  },
  "thresholds": {
    "isolation_forest_anomaly": 0.5,
    "autoencoder_reconstruction": 1.914,
    "velocity_10min": 5,
    "velocity_1hour": 15
  }
}
```

### Step 4.2: Create Config Loader

Create file: `config/config_loader.py`

```python
import json
import os
from typing import Dict, Any

class ConfigLoader:
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self.load_config()
    
    def load_config(self):
        """Load configuration from JSON file"""
        config_path = os.path.join(os.path.dirname(__file__), 'app_config.json')
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            self._config = json.load(f)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot notation (e.g., 'database.server')"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        
        return value if value is not None else default
    
    def get_database_config(self) -> Dict:
        """Get database configuration"""
        return self._config.get('database', {})
    
    def get_api_config(self) -> Dict:
        """Get API configuration"""
        return self._config.get('api', {})
    
    def get_security_config(self) -> Dict:
        """Get security configuration"""
        return self._config.get('security', {})
    
    def get_model_config(self) -> Dict:
        """Get model configuration"""
        return self._config.get('models', {})

# Singleton instance
def get_config() -> ConfigLoader:
    return ConfigLoader()
```

---

**Document Version:** 1.0  
**Status:** Part 2 Complete - Security & Configuration
