# Idempotence Key Implementation Guide

## Overview
Ye document Banking Fraud Detection API mein Idempotence Key implementation ki poori logic explain karta hai.

---

## 1. Idempotence Key Kya Hai?

Idempotence key ek unique identifier hai jo duplicate requests ko identify karta hai.

**Example:**
```
Request 1: POST /api/analyze-transaction
  idempotence_key: "550e8400-e29b-41d4-a716-446655440000"
  Response: APPROVED

Request 2 (Duplicate): POST /api/analyze-transaction
  idempotence_key: "550e8400-e29b-41d4-a716-446655440000"
  Response: APPROVED (cached - naya processing nahi)
```

---

## 2. Flow Diagram

```
Client Request
    ↓
Check IdempotenceKey in TransactionLogs
    ↓
    ┌─────────────────────────────────────┐
    │ Key Found + IsSuccessful = 1?       │
    └─────────────────────────────────────┘
         YES ↓                    ↓ NO
    Return Cached          Process New
    Response               Transaction
         ↓                        ↓
    Log as Cached          Execute Logic
    (is_cached=true)       (Fraud Detection)
                               ↓
                          Store Result
                               ↓
                          Insert Log Entry
                          (is_cached=false)
```

---

## 3. Implementation Details

### Step 1: TransactionRequest Model

```python
class TransactionRequest(BaseModel):
    customer_id: str
    from_account_no: str
    from_account_currency: str
    to_account_no: str
    transaction_amount: float
    transfer_currency: str
    transfer_type: str
    charges_type: Optional[str] = ""
    swift: Optional[str] = ""
    check_constraint: bool = True
    datetime: Optional[datetime] = None
    bank_country: Optional[str] = "UAE"
    idempotence_key: Optional[str] = None
```

**idempotence_key:**
- Optional field
- Client se aaye ya auto-generate ho
- UUID format mein

### Step 2: Database Schema

TransactionLogs table mein ye columns hain:

| Column | Type | Purpose |
|--------|------|---------|
| LogID | BIGINT | Unique log identifier |
| IdempotenceKey | UNIQUEIDENTIFIER | Unique request identifier |
| RequestTimestamp | DATETIME2 | Request receive time |
| ResponseTimestamp | DATETIME2 | Response send time |
| ExecutionTimeMs | INT | Processing time |
| RequestMethod | NVARCHAR | HTTP method (POST, GET) |
| RequestEndpoint | NVARCHAR | API endpoint |
| RequestPayload | NVARCHAR(MAX) | Full request body (JSON) |
| ResponsePayload | NVARCHAR(MAX) | Full response body (JSON) |
| ResponseStatusCode | INT | HTTP status code |
| IsSuccessful | BIT | Success flag (1=success, 0=failure) |
| UserID | NVARCHAR | User/Customer ID |
| RiskScore | FLOAT | Fraud risk score |
| Decision | NVARCHAR | Decision (APPROVED, FLAGGED, BLOCKED) |
| CreatedAt | DATETIME | Log creation time |

### Step 3: Helper Functions

#### generate_idempotence_key()
```python
def generate_idempotence_key() -> str:
    return str(uuid.uuid4())
```

Auto-generate karta hai UUID format mein.

#### check_idempotence()
```python
def check_idempotence(idempotence_key: str) -> dict:
    db = get_db_service()
    
    try:
        if not db.connect():
            return None
        
        cached_log = db.get_transaction_log_by_idempotence_key(idempotence_key)
        
        if cached_log:
            return {
                "is_duplicate": True,
                "decision": cached_log.get('Decision'),
                "risk_score": cached_log.get('RiskScore'),
                "response_payload": cached_log.get('ResponsePayload'),
                "log_id": cached_log.get('LogID')
            }
        
        return {"is_duplicate": False}
    except Exception as e:
        logger.error(f"Error checking idempotence: {e}")
        return None
    finally:
        db.disconnect()
```

Database mein check karta hai key pehle se exist karta hai ya nahi.

### Step 4: API Endpoint Logic

```python
@app.post("/api/analyze-transaction", response_model=TransactionResponse)
def analyze_transaction(request: TransactionRequest, req: Request):
    verify_basic_auth(req)
    start_time = datetime.now()
    
    if request.datetime is None:
        request.datetime = datetime.now()
    
    idempotence_key = request.idempotence_key or generate_idempotence_key()
    
    cached = check_idempotence(idempotence_key)
    if cached and cached.get("is_duplicate"):
        response_payload = cached.get("response_payload")
        if response_payload:
            response_data = json.loads(response_payload)
            response_data["idempotence_key"] = idempotence_key
            response_data["is_cached"] = True
            return TransactionResponse(**response_data)
    
    validate_transfer_request(request)
    
    # Fraud detection logic
    result = make_decision(txn, user_stats, model, features, autoencoder)
    
    # Save to database
    save_transaction_to_file(
        request=request,
        decision=decision,
        risk_score=result.get('risk_score', 0.0),
        reasons=result.get('reasons', []),
        transaction_id=transaction_id,
        result=result,
        idempotence_key=idempotence_key
    )
    
    return TransactionResponse(
        advice=decision,
        risk_score=result.get('risk_score', 0.0),
        risk_level=result.get('risk_level', 'SAFE'),
        confidence_level=result.get('confidence_level', 0.0),
        model_agreement=result.get('model_agreement', 0.0),
        reasons=result.get('reasons', []),
        individual_scores=result['individual_scores'],
        transaction_id=transaction_id,
        processing_time_ms=processing_time,
        idempotence_key=idempotence_key,
        is_cached=False
    )
```

---

## 4. Request-Response Flow

### Scenario 1: First Request (New)

```
Client Request:
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
  "bank_country": "UAE",
  "idempotence_key": null
}

Server Processing:
1. Auth verify
2. IdempotenceKey generate: "550e8400-e29b-41d4-a716-446655440000"
3. Check database - key nahi milta
4. Fraud detection run
5. TransactionLogs mein INSERT
6. Response return

Response:
{
  "advice": "APPROVED",
  "risk_score": 0.25,
  "risk_level": "SAFE",
  "confidence_level": 0.95,
  "model_agreement": 0.87,
  "reasons": [],
  "individual_scores": {...},
  "transaction_id": "txn_abc12345",
  "processing_time_ms": 245,
  "idempotence_key": "550e8400-e29b-41d4-a716-446655440000",
  "is_cached": false
}

Database Entry:
IdempotenceKey: 550e8400-e29b-41d4-a716-446655440000
IsSuccessful: 1
Decision: APPROVED
RiskScore: 0.25
ResponsePayload: {...full response...}
```

### Scenario 2: Duplicate Request (Cached)

```
Client Request (Same as before):
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
  "bank_country": "UAE",
  "idempotence_key": "550e8400-e29b-41d4-a716-446655440000"
}

Server Processing:
1. Auth verify
2. IdempotenceKey: "550e8400-e29b-41d4-a716-446655440000"
3. Check database - KEY FOUND!
4. IsSuccessful = 1 - YES
5. Return cached response (NO fraud detection)
6. Processing time: ~5ms (vs 245ms pehle)

Response (Cached):
{
  "advice": "APPROVED",
  "risk_score": 0.25,
  "risk_level": "SAFE",
  "confidence_level": 0.95,
  "model_agreement": 0.87,
  "reasons": [],
  "individual_scores": {...},
  "transaction_id": "txn_abc12345",
  "processing_time_ms": 245,
  "idempotence_key": "550e8400-e29b-41d4-a716-446655440000",
  "is_cached": true
}

Database Entry:
NO NEW ENTRY - pehle wala response return kiya
```

---

## 5. Benefits

| Benefit | Description |
|---------|-------------|
| Duplicate Prevention | Same request dobara process nahi hota |
| Performance | Cached response instantly return hota hai |
| Data Integrity | Duplicate transactions database mein nahi aate |
| Audit Trail | Har request ka complete log store hota hai |
| Retry Safety | Client safely retry kar sakta hai |

---

## 6. Postman Testing

### Setup Variables

```
base_url: http://localhost:8000
auth_header: Basic RkRTOjEyMzQ1
idempotence_key: 550e8400-e29b-41d4-a716-446655440000
```

### Test Request 1 (New)

```
POST {{base_url}}/api/analyze-transaction
Authorization: {{auth_header}}
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
  "bank_country": "UAE",
  "idempotence_key": null
}

Response:
{
  "is_cached": false,
  "idempotence_key": "550e8400-e29b-41d4-a716-446655440000",
  "processing_time_ms": 245
}
```

### Test Request 2 (Duplicate)

```
POST {{base_url}}/api/analyze-transaction
Authorization: {{auth_header}}
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
  "bank_country": "UAE",
  "idempotence_key": "550e8400-e29b-41d4-a716-446655440000"
}

Response:
{
  "is_cached": true,
  "idempotence_key": "550e8400-e29b-41d4-a716-446655440000",
  "processing_time_ms": 245
}
```

---

## 7. Database Queries

### Check Idempotence Key

```sql
SELECT * FROM TransactionLogs 
WHERE IdempotenceKey = '550e8400-e29b-41d4-a716-446655440000' 
AND IsSuccessful = 1
ORDER BY CreatedAt DESC
```

### View All Logs

```sql
SELECT 
  LogID,
  IdempotenceKey,
  RequestTimestamp,
  ResponseTimestamp,
  ExecutionTimeMs,
  RequestEndpoint,
  Decision,
  IsSuccessful
FROM TransactionLogs
ORDER BY CreatedAt DESC
```

### Find Duplicate Requests

```sql
SELECT 
  IdempotenceKey,
  COUNT(*) as RequestCount,
  MIN(CreatedAt) as FirstRequest,
  MAX(CreatedAt) as LastRequest
FROM TransactionLogs
GROUP BY IdempotenceKey
HAVING COUNT(*) > 1
```

---

## 8. Error Scenarios

### Scenario 1: Invalid IdempotenceKey Format

```
Request:
{
  "idempotence_key": "invalid-format"
}

Result:
- Server auto-generate karega naya UUID
- Request process hoga normally
```

### Scenario 2: Duplicate Request with Different Data

```
Request 1:
{
  "transaction_amount": 750,
  "idempotence_key": "550e8400-e29b-41d4-a716-446655440000"
}

Request 2 (Same key, different amount):
{
  "transaction_amount": 1000,
  "idempotence_key": "550e8400-e29b-41d4-a716-446655440000"
}

Result:
- Request 2 cached response return karega
- New amount ignore hoga
- Pehle wala response return hoga
```

---

## 9. Best Practices

1. **Client Side:**
   - Har request ke liye unique idempotence_key generate karo
   - Retry karte waqt same key use karo
   - Key store karo audit trail ke liye

2. **Server Side:**
   - IdempotenceKey ko UNIQUE constraint se protect karo
   - Successful requests ko cache karo
   - Failed requests ko retry allow karo

3. **Monitoring:**
   - Duplicate requests track karo
   - Cache hit rate monitor karo
   - Performance improvement measure karo

---

## 10. Summary

| Component | Purpose |
|-----------|---------|
| IdempotenceKey | Unique request identifier |
| TransactionLogs | Audit trail + cache storage |
| check_idempotence() | Duplicate detection |
| generate_idempotence_key() | UUID generation |
| is_cached flag | Response source indicator |

---

**Document Version:** 1.0
**Last Updated:** February 12, 2026
**Status:** Ready for Implementation
