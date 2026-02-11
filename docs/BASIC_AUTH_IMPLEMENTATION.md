# Basic Authentication Implementation Guide

## Overview
Ye document Banking Fraud Detection API mein Basic Authentication implementation ki poori logic explain karta hai.

---

## 1. Authentication Flow Diagram

```
Client Request
    ↓
Authorization Header Check
    ↓
Base64 Decode (username:password)
    ↓
Environment Variables se Match
    ↓
✓ Match → Request Process → Database Save
✗ No Match → 401 Unauthorized Error
```

---

## 2. Step-by-Step Implementation

### Step 1: Environment Variables Setup (.env file)

```
API_USERNAME=FDS
API_PASSWORD=12345
```

**Kya hota hai:**
- Ye credentials server-side mein store hote hain
- Client ko ye credentials bhejne padte hain har request mein
- Credentials environment variables se load hote hain (secure way)

---

### Step 2: Docker Configuration (docker-compose.yml)

```yaml
environment:
  - API_USERNAME=FDS
  - API_PASSWORD=12345
  - DB_SERVER=10.112.32.4
  - DB_PORT=1433
  - DB_DATABASE=retailchannelLogs
  - DB_USERNAME=dbuser
  - DB_PASSWORD=Codebase202212?!
```

**Kya hota hai:**
- Docker container start hote waqt ye environment variables set hote hain
- Container ke andar Python code ko ye variables access kar sakte hain `os.getenv()` se
- Database aur API dono ke credentials container ko available hote hain

---

### Step 3: Helper Function (api/helpers.py)

```python
def verify_basic_auth(request: Request):
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Basic "):
        raise HTTPException(status_code=401, detail="authentication failed try again")
    
    try:
        encoded_credentials = auth_header.split(" ")[1]
        decoded = base64.b64decode(encoded_credentials).decode("utf-8")
        username, password = decoded.split(":", 1)
    except:
        raise HTTPException(status_code=401, detail="authentication failed try again")
    
    expected_username = os.getenv("API_USERNAME")
    expected_password = os.getenv("API_PASSWORD")
    
    if username != expected_username or password != expected_password:
        raise HTTPException(status_code=401, detail="authentication failed try again")
    
    return True
```

**Kya hota hai:**

1. **Authorization Header Extract**
   - Request ke headers se "Authorization" field nikalta hai
   - Format: `Authorization: Basic RkRTOjEyMzQ1`

2. **Base64 Decode**
   - `RkRTOjEyMzQ1` ko decode karta hai
   - Result: `FDS:12345` (username:password)

3. **Credentials Split**
   - Colon (`:`) se split karke username aur password alag karta hai
   - Username: `FDS`
   - Password: `12345`

4. **Environment Variables se Match**
   - `os.getenv("API_USERNAME")` → `FDS`
   - `os.getenv("API_PASSWORD")` → `12345`
   - Agar match ho toh ✓ success
   - Agar match na ho toh ✗ 401 error

---

### Step 4: Endpoint Protection (api/api.py)

```python
@app.post("/api/analyze-transaction", response_model=TransactionResponse)
def analyze_transaction(request: TransactionRequest, req: Request):
    verify_basic_auth(req)  # ← Auth check pehle
    start_time = datetime.now()
    
    # Baaki logic...
```

**Kya hota hai:**

1. Client request bhejta hai
2. Endpoint execute hone se pehle `verify_basic_auth(req)` call hota hai
3. Agar auth fail ho toh 401 error return hota hai
4. Agar auth success ho toh request process hota hai

**Protected Endpoints:**
- ✓ `/api/analyze-transaction` - Transaction analysis
- ✓ `/api/transaction/approve` - Transaction approval
- ✓ `/api/transaction/reject` - Transaction rejection
- ✓ `/api/transactions/pending` - Pending transactions list
- ✓ `/api/features` - Features list
- ✓ `/api/features/{name}/enable` - Enable feature
- ✓ `/api/features/{name}/disable` - Disable feature

**Public Endpoints (bina auth):**
- ✓ `/api/health` - Health check

---

## 3. Complete Request-Response Flow

### Scenario: Transaction Analysis Request

#### Step 1: Client Prepares Request

```
POST /api/analyze-transaction
Authorization: Basic RkRTOjEyMzQ1
Content-Type: application/json

{
  "customer_id": "1000016",
  "from_account_no": "011000016033",
  "from_account_currency": "AED",
  "to_account_no": "011000016019",
  "transaction_amount": 750,
  "transfer_currency": "AED",
  "transfer_type": "O",
  "charges_type": "SHA",
  "swift": "DEUTDEFJ",
  "check_constraint": true,
  "bank_country": "UAE"
}
```

#### Step 2: Server Receives Request

```
FastAPI receives request
↓
Endpoint function calls verify_basic_auth(req)
↓
verify_basic_auth extracts Authorization header
↓
Base64 decode: RkRTOjEyMzQ1 → FDS:12345
↓
Match with environment variables
↓
✓ FDS == FDS ✓ 12345 == 12345
↓
Auth Success! Continue processing
```

#### Step 3: Transaction Processing

```
validate_transfer_request(request)
↓
Get user statistics from database
↓
Check if beneficiary is new
↓
Get velocity data from CSV
↓
Run fraud detection models:
  - Rule Engine
  - Isolation Forest
  - Autoencoder
↓
Generate risk score and decision
↓
Save to database (APITransactionLogs table)
```

#### Step 4: Database Save

```python
save_transaction_to_file(
    request=request,
    decision=decision,
    risk_score=result.get('risk_score', 0.0),
    reasons=result.get('reasons', []),
    transaction_id=transaction_id,
    result=result
)
```

**Database Query:**
```sql
INSERT INTO APITransactionLogs (
    TransactionId, CustomerId, FromAccountNo, FromAccountCurrency,
    ToAccountNo, Amount, TransferCurrency, TransferType, ChargesType,
    SwiftCode, CheckConstraint, BankCountry, Advice, RiskScore,
    RiskLevel, ConfidenceLevel, ModelAgreement, Reasons,
    RuleEngineViolated, RuleEngineThreshold, IsolationForestScore,
    IsolationForestAnomaly, AutoencoderError, AutoencoderThreshold,
    AutoencoderAnomaly, UserAction, ProcessingTimeMs
) VALUES (...)
```

#### Step 5: Response to Client

```json
{
  "advice": "APPROVED",
  "risk_score": 0.25,
  "risk_level": "SAFE",
  "confidence_level": 0.95,
  "model_agreement": 0.87,
  "reasons": [],
  "individual_scores": {
    "rule_engine": {...},
    "isolation_forest": {...},
    "autoencoder": {...}
  },
  "transaction_id": "txn_abc12345",
  "processing_time_ms": 245
}
```

---

## 4. Database Table Structure

### APITransactionLogs Table

| Column | Type | Purpose |
|--------|------|---------|
| TransactionId | VARCHAR | Unique transaction identifier |
| CustomerId | VARCHAR | Customer ID from request |
| FromAccountNo | VARCHAR | Source account number |
| FromAccountCurrency | VARCHAR | Source currency (AED, USD, etc.) |
| ToAccountNo | VARCHAR | Destination account number |
| Amount | DECIMAL | Transaction amount |
| TransferCurrency | VARCHAR | Transfer currency |
| TransferType | VARCHAR | Type (O=Outbound, I=Inbound, S=SWIFT) |
| ChargesType | VARCHAR | Charges type (OUR, BEN, SHA) |
| SwiftCode | VARCHAR | SWIFT code for international transfers |
| CheckConstraint | BIT | Constraint check flag |
| BankCountry | VARCHAR | Bank country code |
| Advice | VARCHAR | Decision (APPROVED, REQUIRES_USER_APPROVAL, etc.) |
| RiskScore | DECIMAL | Overall risk score (0-1) |
| RiskLevel | VARCHAR | Risk level (SAFE, LOW, MEDIUM, HIGH) |
| ConfidenceLevel | DECIMAL | Model confidence (0-1) |
| ModelAgreement | DECIMAL | Agreement between models (0-1) |
| Reasons | TEXT | Fraud reasons (pipe-separated) |
| RuleEngineViolated | BIT | Rule engine violation flag |
| RuleEngineThreshold | DECIMAL | Rule engine threshold |
| IsolationForestScore | DECIMAL | Isolation Forest anomaly score |
| IsolationForestAnomaly | BIT | Is anomaly detected |
| AutoencoderError | DECIMAL | Autoencoder reconstruction error |
| AutoencoderThreshold | DECIMAL | Autoencoder threshold |
| AutoencoderAnomaly | BIT | Is anomaly detected |
| UserAction | VARCHAR | User action (PENDING, APPROVED, REJECTED) |
| ProcessingTimeMs | INT | Processing time in milliseconds |

---

## 5. Error Scenarios

### Scenario 1: No Authorization Header

```
Request:
POST /api/analyze-transaction
Content-Type: application/json
{...}

Response:
401 Unauthorized
{
  "detail": "authentication failed try again"
}
```

### Scenario 2: Invalid Base64

```
Request:
Authorization: Basic !!!invalid!!!

Response:
401 Unauthorized
{
  "detail": "authentication failed try again"
}
```

### Scenario 3: Wrong Credentials

```
Request:
Authorization: Basic d3Jvbmc6d3Jvbmc=  (wrong:wrong)

Response:
401 Unauthorized
{
  "detail": "authentication failed try again"
}
```

### Scenario 4: Correct Credentials

```
Request:
Authorization: Basic RkRTOjEyMzQ1  (FDS:12345)

Response:
200 OK
{
  "advice": "APPROVED",
  "risk_score": 0.25,
  ...
}

Database:
INSERT INTO APITransactionLogs VALUES (...)
```

---

## 6. Postman Testing

### Setup Variables

```
base_url: http://localhost:8000
auth_header: Basic RkRTOjEyMzQ1
```

### Test Request

```
POST {{base_url}}/api/analyze-transaction
Authorization: {{auth_header}}
Content-Type: application/json

{
  "customer_id": "1000016",
  "from_account_no": "011000016033",
  ...
}
```

---

## 7. Docker Deployment

### Build Image

```bash
docker build -f Docker/Dockerfile -t fraud-detection-api .
```

### Run Container

```bash
docker-compose -f Docker/docker-compose.yml up -d
```

### Environment Variables in Container

```
API_USERNAME=FDS
API_PASSWORD=12345
DB_SERVER=10.112.32.4
DB_PORT=1433
DB_DATABASE=retailchannelLogs
DB_USERNAME=dbuser
DB_PASSWORD=Codebase202212?!
```

---

## 8. Security Notes

1. **Credentials in .env**: Production mein `.env` file git mein commit na karo
2. **HTTPS Required**: Production mein HTTPS use karo (HTTP nahi)
3. **Base64 Not Encryption**: Base64 sirf encoding hai, encryption nahi
4. **Password Strength**: Strong passwords use karo
5. **Environment Variables**: Docker/production mein secure way se set karo

---

## 9. Summary

| Component | Purpose |
|-----------|---------|
| `.env` file | Credentials store karna |
| `docker-compose.yml` | Environment variables set karna |
| `verify_basic_auth()` | Auth logic implement karna |
| `api/api.py` endpoints | Auth check add karna |
| `postman_collection.json` | Testing ke liye auth headers |
| Database | Transaction data save karna |

---

## 10. Next Steps

- Indempotency Key implementation
- Rate limiting
- Token-based authentication (JWT)
- Role-based access control (RBAC)
