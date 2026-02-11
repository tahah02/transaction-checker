import logging
from api.models import TransactionRequest
from typing import List, Dict, Any
from fastapi import HTTPException, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import base64
import os

logger = logging.getLogger(__name__)


def validate_transfer_request(request: TransactionRequest):
    if request.transfer_type in ['O', 'I']:
        if not request.to_account_no or request.to_account_no.strip() == "":
            raise HTTPException(status_code=400, detail=f"to_account_no required for transfer type {request.transfer_type}")
    
    if request.transfer_type == 'S':
        if not request.swift or request.swift.strip() == "":
            raise HTTPException(status_code=400, detail="SWIFT code required for international transfers")
    
    valid_currencies = ['AED', 'USD', 'EUR', 'GBP', 'SAR', 'QAR', 'OMR', 'KWD', 'BHD']
    if request.from_account_currency not in valid_currencies:
        raise HTTPException(status_code=400, detail=f"Invalid from_account_currency: {request.from_account_currency}")
    
    if request.transfer_currency not in valid_currencies:
        raise HTTPException(status_code=400, detail=f"Invalid transfer_currency: {request.transfer_currency}")
    
    if request.charges_type and request.charges_type not in ['OUR', 'BEN', 'SHA', '']:
        raise HTTPException(status_code=400, detail="charges_type must be OUR, BEN, SHA or empty")
    
    return True


def save_transaction_to_file(request: TransactionRequest, decision: str, risk_score: float, reasons: List[str], transaction_id: str, result: Dict[str, Any] = None):
    from backend.db_service import get_db_service
    db = get_db_service()
    
    try:
        if not db.connect():
            raise Exception("Database connection failed")
        
        scores = result.get('individual_scores', {}) if result else {}
        re = scores.get('rule_engine', {})
        if_score = scores.get('isolation_forest', {})
        ae = scores.get('autoencoder', {})
        
        query = """INSERT INTO APITransactionLogs (
            TransactionId, CustomerId, FromAccountNo, FromAccountCurrency, ToAccountNo, Amount, TransferCurrency, TransferType, ChargesType,
            SwiftCode, CheckConstraint, BankCountry, Advice, RiskScore, RiskLevel, ConfidenceLevel, ModelAgreement, Reasons,
            RuleEngineViolated, RuleEngineThreshold, IsolationForestScore, IsolationForestAnomaly,
            AutoencoderError, AutoencoderThreshold, AutoencoderAnomaly, UserAction, ProcessingTimeMs
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        
        params = [
            transaction_id, request.customer_id, request.from_account_no, request.from_account_currency,
            request.to_account_no, float(request.transaction_amount), request.transfer_currency, request.transfer_type,
            request.charges_type or '', request.swift or '', 1 if request.check_constraint else 0, request.bank_country or 'UAE',
            decision, float(risk_score), result.get('risk_level', 'SAFE') if result else 'SAFE',
            float(result.get('confidence_level', 0.0)) if result else 0.0, float(result.get('model_agreement', 0.0)) if result else 0.0,
            ' | '.join(reasons) if reasons else '', 1 if re.get('violated', False) else 0, float(re.get('threshold', 0.0)),
            float(if_score.get('anomaly_score', 0.0)), 1 if if_score.get('is_anomaly', False) else 0,
            float(ae.get('reconstruction_error', 0.0)) if ae.get('reconstruction_error') is not None else None,
            float(ae.get('threshold', 0.0)) if ae.get('threshold') is not None else None, 1 if ae.get('is_anomaly', False) else 0,
            'PENDING' if decision in ['REQUIRES_USER_APPROVAL', 'BLOCK_AND_VERIFY'] else 'APPROVED',
            int(result.get('processing_time_ms', 0)) if result else 0
        ]
        
        db.execute_non_query(query, params)
        logger.info(f"Transaction {transaction_id} saved")
    except Exception as e:
        logger.error(f"Save transaction failed: {e}")
    finally:
        db.disconnect()


def update_transaction_status(transaction_id: str, action: str, actioned_by: str, comments: str = "") -> bool:
    from backend.db_service import get_db_service
    db = get_db_service()
    
    try:
        if not db.connect():
            logger.error("Database connection failed")
            return False
        
        query = "UPDATE APITransactionLogs SET UserAction = %s, ActionedBy = %s, ActionTimestamp = GETDATE(), ActionComments = %s WHERE TransactionId = %s"
        db.execute_non_query(query, [action, actioned_by, comments, transaction_id])
        logger.info(f"Transaction {transaction_id} updated to {action}")
        return True
    except Exception as e:
        logger.error(f"Update transaction failed: {e}")
        return False
    finally:
        db.disconnect()


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
