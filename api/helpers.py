import pandas as pd
import logging
import csv
import os
from datetime import datetime
from api.models import TransactionRequest
from typing import List, Dict, Any
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def validate_transfer_request(request: TransactionRequest):
    """Validate transfer request based on transfer type"""
    
    # Transfer type O (Own) or I (Internal) - to_account_no required
    if request.transfer_type in ['O', 'I']:
        if not request.to_account_no or request.to_account_no.strip() == "":
            raise HTTPException(
                status_code=400,
                detail=f"to_account_no is required for transfer type {request.transfer_type}"
            )
    
    # Transfer type S (International) - SWIFT code required
    if request.transfer_type == 'S':
        if not request.swift or request.swift.strip() == "":
            raise HTTPException(
                status_code=400,
                detail="SWIFT code is required for international transfers"
            )
    
    # Currency validation
    valid_currencies = ['AED', 'USD', 'EUR', 'GBP', 'SAR', 'QAR', 'OMR', 'KWD', 'BHD']
    if request.from_account_currency not in valid_currencies:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid from_account_currency. Must be one of: {', '.join(valid_currencies)}"
        )
    
    if request.transfer_currency not in valid_currencies:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transfer_currency. Must be one of: {', '.join(valid_currencies)}"
        )
    
    # Charges type validation (if provided)
    if request.charges_type and request.charges_type not in ['OUR', 'BEN', 'SHA', '']:
        raise HTTPException(
            status_code=400,
            detail="charges_type must be one of: OUR, BEN, SHA or empty"
        )
    
    return True


def save_transaction_to_file(request: TransactionRequest, decision: str, risk_score: float, reasons: List[str], transaction_id: str, result: Dict[str, Any] = None):
    from backend.db_service import get_db_service
    db = get_db_service()
    
    try:
        if not db.connect():
            raise Exception("Database connection failed")
        
        individual_scores = result.get('individual_scores', {}) if result else {}
        rule_engine = individual_scores.get('rule_engine', {})
        isolation_forest = individual_scores.get('isolation_forest', {})
        autoencoder = individual_scores.get('autoencoder', {})
        
        query = """
            INSERT INTO APITransactionLogs (
                TransactionId, CustomerId, FromAccountNo, FromAccountCurrency,
                ToAccountNo, Amount, TransferCurrency, TransferType, ChargesType,
                SwiftCode, CheckConstraint, BankCountry, Decision, RiskScore,
                RiskLevel, ConfidenceLevel, ModelAgreement, Reasons,
                RuleEngineViolated, RuleEngineThreshold,
                IsolationForestScore, IsolationForestAnomaly,
                AutoencoderError, AutoencoderThreshold, AutoencoderAnomaly,
                UserAction, ProcessingTimeMs
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = [
            transaction_id,
            request.customer_id,
            request.from_account_no,
            request.from_account_currency,
            request.to_account_no,
            float(request.transaction_amount),
            request.transfer_currency,
            request.transfer_type,
            request.charges_type or '',
            request.swift or '',
            1 if request.check_constraint else 0,
            request.bank_country or 'UAE',
            decision,
            float(risk_score),
            result.get('risk_level', 'SAFE') if result else 'SAFE',
            float(result.get('confidence_level', 0.0)) if result else 0.0,
            float(result.get('model_agreement', 0.0)) if result else 0.0,
            ' | '.join(reasons) if reasons else '',
            1 if rule_engine.get('violated', False) else 0,
            float(rule_engine.get('threshold', 0.0)),
            float(isolation_forest.get('anomaly_score', 0.0)),
            1 if isolation_forest.get('is_anomaly', False) else 0,
            float(autoencoder.get('reconstruction_error', 0.0)) if autoencoder.get('reconstruction_error') is not None else None,
            float(autoencoder.get('threshold', 0.0)) if autoencoder.get('threshold') is not None else None,
            1 if autoencoder.get('is_anomaly', False) else 0,
            'PENDING' if decision == 'REQUIRES_USER_APPROVAL' else None,
            int(result.get('processing_time_ms', 0)) if result else 0
        ]
        
        db.execute_non_query(query, params)
        logger.info(f"Transaction {transaction_id} saved to database")
    except Exception as e:
        logger.error(f"Failed to save transaction to database: {e}")
    finally:
        db.disconnect()


def update_transaction_status(transaction_id: str, action: str, actioned_by: str, comments: str = "") -> bool:
    from backend.db_service import get_db_service
    db = get_db_service()
    
    try:
        if not db.connect():
            logger.error("Database connection failed")
            return False
        
        query = """
            UPDATE APITransactionLogs
            SET UserAction = %s,
                ActionedBy = %s,
                ActionTimestamp = GETDATE(),
                ActionComments = %s
            WHERE TransactionId = %s
        """
        
        params = [action, actioned_by, comments, transaction_id]
        
        result = db.execute_non_query(query, params)
        logger.info(f"Transaction {transaction_id} updated to {action} by {actioned_by}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update transaction status: {e}")
        return False
    finally:
        db.disconnect()
