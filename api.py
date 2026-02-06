from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np
import uuid
import logging
import csv
import os
from backend.hybrid_decision import make_decision
from backend.utils import load_model
from backend.autoencoder import AutoencoderInference
from backend.rule_engine import calculate_all_limits
from backend.db_service import get_db_service

logger = logging.getLogger(__name__)
app = FastAPI(title="Banking Fraud Detection API", version="1.0.0")
db = get_db_service()

class TransactionRequest(BaseModel):
    customer_id: str
    from_account_no: str
    to_account_no: str
    transaction_amount: float = Field(gt=0)
    transfer_type: str = Field(pattern="^[SILQO]$")
    datetime: datetime
    bank_country: Optional[str] = "UAE"

class TransactionResponse(BaseModel):
    decision: str
    risk_score: float
    confidence_level: float
    reasons: List[str]
    individual_scores: dict
    transaction_id: str
    processing_time_ms: int

class ApprovalRequest(BaseModel):
    transaction_id: str
    customer_id: str
    comments: Optional[str] = ""

class RejectionRequest(BaseModel):
    transaction_id: str
    customer_id: str
    reason: str

class ActionResponse(BaseModel):
    status: str
    transaction_id: str
    timestamp: str
    message: str

model, features, scaler = load_model()
autoencoder = AutoencoderInference()
autoencoder.load()


def save_transaction_to_file(request: TransactionRequest, decision: str, risk_score: float, reasons: List[str], transaction_id: str):
    try:
        file_path = 'data/api_transactions.csv'
        file_exists = os.path.isfile(file_path)
        
        with open(file_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            if not file_exists:
                writer.writerow([
                    'Timestamp', 'Customer_ID', 'From_Account', 'To_Account',
                    'Amount', 'Transfer_Type', 'Bank_Country', 'Decision',
                    'Risk_Score', 'Reasons', 'Transaction_ID',
                    'User_Action', 'Actioned_By', 'Action_Timestamp', 'Action_Comments'
                ])
            
            writer.writerow([
                datetime.now().isoformat(),
                request.customer_id,
                request.from_account_no,
                request.to_account_no,
                request.transaction_amount,
                request.transfer_type,
                request.bank_country,
                decision,
                risk_score,
                ' | '.join(reasons),
                transaction_id,
                'PENDING',  # User_Action
                '',         # Actioned_By
                '',         # Action_Timestamp
                ''          # Action_Comments
            ])
        
        logger.info(f"Transaction {transaction_id} saved to {file_path}")
    except Exception as e:
        logger.error(f"Failed to save transaction to file: {e}")
        # Don't raise - we don't want to fail the API call if file save fails


def update_transaction_status(transaction_id: str, action: str, actioned_by: str, comments: str = "") -> bool:
    try:
        file_path = 'data/api_transactions.csv'
        
        if not os.path.isfile(file_path):
            logger.error(f"Transaction file not found: {file_path}")
            return False
        
        df = pd.read_csv(file_path)
        mask = df['Transaction_ID'] == transaction_id
        
        if not mask.any():
            logger.error(f"Transaction not found: {transaction_id}")
            return False
        
        df.loc[mask, 'User_Action'] = action
        df.loc[mask, 'Actioned_By'] = actioned_by
        df.loc[mask, 'Action_Timestamp'] = datetime.now().isoformat()
        df.loc[mask, 'Action_Comments'] = comments
        
        df.to_csv(file_path, index=False)
        logger.info(f"Transaction {transaction_id} updated to {action} by {actioned_by}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update transaction status: {e}")
        return False


def get_velocity_from_csv(customer_id: str, account_no: str) -> Dict[str, int]:
    try:
        file_path = 'data/api_transactions.csv'
        if not os.path.isfile(file_path):
            return {"txn_count_10min": 0, "txn_count_1hour": 0}
        
        df = pd.read_csv(file_path)
        
        customer_id_str = str(customer_id)
        account_no_str = str(account_no).lstrip('0')
        
        customer_match = df['Customer_ID'].astype(str) == customer_id_str
        account_match = df['From_Account'].astype(str).str.lstrip('0') == account_no_str
        
        df = df[customer_match & account_match]
        
        if len(df) == 0:
            return {"txn_count_10min": 0, "txn_count_1hour": 0}
        
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        now = datetime.now()
        
        ten_min_ago = now - timedelta(minutes=10)
        txn_10min = len(df[df['Timestamp'] >= ten_min_ago])
        
        one_hour_ago = now - timedelta(hours=1)
        txn_1hour = len(df[df['Timestamp'] >= one_hour_ago])
        
        return {
            "txn_count_10min": txn_10min,
            "txn_count_1hour": txn_1hour
        }
    except Exception as e:
        logger.error(f"Error getting velocity from CSV: {e}")
        return {"txn_count_10min": 0, "txn_count_1hour": 0}


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
        is_new_ben = db.check_new_beneficiary(request.customer_id, request.to_account_no, request.transfer_type)
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
def get_pending_transactions():
    try:
        file_path = 'data/api_transactions.csv'
        
        if not os.path.isfile(file_path):
            return {"count": 0, "transactions": []}
        
        df = pd.read_csv(file_path)
        pending_df = df[df['User_Action'] == 'PENDING']
        
        transactions = []
        for _, row in pending_df.iterrows():
            try:
                amount = float(row['Amount'])
                if pd.isna(amount) or np.isinf(amount):
                    amount = 0.0
            except:
                amount = 0.0
            
            try:
                risk_score = float(row['Risk_Score'])
                if pd.isna(risk_score) or np.isinf(risk_score):
                    risk_score = 0.0
            except:
                risk_score = 0.0
            
            transactions.append({
                "transaction_id": str(row['Transaction_ID']),
                "customer_id": str(row['Customer_ID']),
                "from_account": str(row['From_Account']),
                "to_account": str(row['To_Account']),
                "amount": amount,
                "transfer_type": str(row['Transfer_Type']),
                "decision": str(row['Decision']),
                "risk_score": risk_score,
                "reasons": str(row['Reasons']),
                "timestamp": str(row['Timestamp'])
            })
        
        return {"count": len(transactions), "transactions": transactions}
        
    except Exception as e:
        logger.error(f"Error fetching pending transactions: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
