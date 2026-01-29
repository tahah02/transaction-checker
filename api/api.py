from fastapi import FastAPI, HTTPException
from datetime import datetime
import uuid
import logging
from backend.hybrid_decision import make_decision
from backend.utils import load_model
from backend.autoencoder import AutoencoderInference
from backend.db_service import get_db_service
from api.models import TransactionRequest, TransactionResponse, ApprovalRequest, RejectionRequest, ActionResponse
from api.services import get_velocity_from_csv, get_pending_transactions
from api.helpers import save_transaction_to_file, update_transaction_status

logger = logging.getLogger(__name__)
app = FastAPI(title="Banking Fraud Detection API", version="1.0.0")
db = get_db_service()

model, features, scaler = load_model()
autoencoder = AutoencoderInference()
autoencoder.load()


@app.get("/api/health")
def health_check():
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


@app.post("/api/analyze-transaction", response_model=TransactionResponse)
def analyze_transaction(request: TransactionRequest):
    start_time = datetime.now()
    
    try:
        db_stats = db.get_all_user_stats(request.customer_id, request.from_account_no)
        user_stats = {
            "user_avg_amount": db_stats.get("user_avg_amount", 5000.0),
            "user_std_amount": db_stats.get("user_std_amount", 2000.0),
            "user_max_amount": db_stats.get("user_max_amount", 15000.0),
            "user_txn_frequency": db_stats.get("user_txn_frequency", 0),
            "user_international_ratio": db_stats.get("user_international_ratio", 0.0),
            "current_month_spending": db_stats.get("current_month_spending", 0.0),
            "user_weekly_total": db_stats.get("user_weekly_total", 0.0),
            "user_weekly_txn_count": db_stats.get("user_weekly_txn_count", 0),
            "user_weekly_avg_amount": db_stats.get("user_weekly_avg_amount", 0.0),
            "user_weekly_deviation": db_stats.get("user_weekly_deviation", 0.0),
            "user_monthly_txn_count": db_stats.get("user_monthly_txn_count", 0),
            "user_monthly_avg_amount": db_stats.get("user_monthly_avg_amount", 0.0),
            "user_monthly_deviation": db_stats.get("user_monthly_deviation", 0.0),
            "txn_count_10min": db_stats.get("txn_count_10min", 0),
            "txn_count_1hour": db_stats.get("txn_count_1hour", 0),
            "time_since_last_txn": db_stats.get("time_since_last_txn", 3600.0)
        }
    except:
        user_stats = {
            "user_avg_amount": 5000.0,
            "user_std_amount": 2000.0,
            "user_max_amount": 15000.0,
            "user_txn_frequency": 0,
            "user_international_ratio": 0.0,
            "current_month_spending": 0.0,
            "user_weekly_total": 0.0,
            "user_weekly_txn_count": 0,
            "user_weekly_avg_amount": 0.0,
            "user_weekly_deviation": 0.0,
            "user_monthly_txn_count": 0,
            "user_monthly_avg_amount": 0.0,
            "user_monthly_deviation": 0.0,
            "txn_count_10min": 0,
            "txn_count_1hour": 0,
            "time_since_last_txn": 3600.0
        }
    
    try:
        is_new_ben = db.check_new_beneficiary(request.customer_id, request.to_account_no)
    except Exception as e:
        logger.error(f"Beneficiary check failed - database unavailable: {e}")
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable - unable to verify beneficiary. Please try again."
        )
    
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
    
    save_transaction_to_file(
        request=request,
        decision=decision,
        risk_score=result.get('risk_score', 0.0),
        reasons=result.get('reasons', []),
        transaction_id=transaction_id
    )
    
    return TransactionResponse(
        decision=decision,
        risk_score=result.get('risk_score', 0.0),
        confidence_level=0.85,
        reasons=result.get('reasons', []),
        individual_scores={
            "rule_engine": {"violated": result['is_fraud'], "threshold": result.get('threshold', 0)},
            "isolation_forest": {"anomaly_score": result.get('risk_score', 0), "is_anomaly": result.get('ml_flag', False)},
            "autoencoder": {"reconstruction_error": result.get('ae_reconstruction_error'), "is_anomaly": result.get('ae_flag', False)}
        },
        transaction_id=transaction_id,
        processing_time_ms=processing_time
    )


@app.post("/api/transaction/approve", response_model=ActionResponse)
def approve_transaction(request: ApprovalRequest):
    try:
        success = update_transaction_status(
            transaction_id=request.transaction_id,
            action="APPROVED",
            actioned_by=request.customer_id,
            comments=request.comments
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Transaction {request.transaction_id} not found or update failed"
            )
        
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
def reject_transaction(request: RejectionRequest):
    try:
        success = update_transaction_status(
            transaction_id=request.transaction_id,
            action="REJECTED",
            actioned_by=request.customer_id,
            comments=request.reason
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Transaction {request.transaction_id} not found or update failed"
            )
        
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


@app.get("/api/transactions/pending")
def list_pending_transactions():
    return get_pending_transactions()
