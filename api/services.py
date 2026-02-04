import pandas as pd
import numpy as np
import logging
import os
from datetime import datetime, timedelta
from typing import Dict
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def get_velocity_from_csv(customer_id: str, account_no: str) -> Dict[str, int]:
    logger.info(f"VELOCITY CHECK CALLED for {customer_id}/{account_no}")
    from backend.db_service import get_db_service
    db = get_db_service()
    
    try:
        if not db.connect():
            logger.error("Database connection failed for velocity check")
            return {"txn_count_10min": 0, "txn_count_1hour": 0}
        
        query_10min = """
            SELECT COUNT(*) as count
            FROM APITransactionLogs
            WHERE CustomerId = %s 
              AND FromAccountNo = %s
              AND CreatedAt >= DATEADD(MINUTE, -10, GETDATE())
        """
        
        query_1hour = """
            SELECT COUNT(*) as count
            FROM APITransactionLogs
            WHERE CustomerId = %s 
              AND FromAccountNo = %s
              AND CreatedAt >= DATEADD(HOUR, -1, GETDATE())
        """
        
        df_10min = db.execute_query(query_10min, [customer_id, account_no])
        df_1hour = db.execute_query(query_1hour, [customer_id, account_no])
        
        txn_10min = int(df_10min['count'].iloc[0]) if len(df_10min) > 0 else 0
        txn_1hour = int(df_1hour['count'].iloc[0]) if len(df_1hour) > 0 else 0
        
        logger.info(f"Velocity: {customer_id}/{account_no} -> 10min={txn_10min}, 1hour={txn_1hour}")
        
        return {
            "txn_count_10min": txn_10min,
            "txn_count_1hour": txn_1hour
        }
    except Exception as e:
        logger.error(f"Error getting velocity from database: {e}")
        return {"txn_count_10min": 0, "txn_count_1hour": 0}
    finally:
        db.disconnect()


def get_pending_transactions():
    from backend.db_service import get_db_service
    db = get_db_service()
    
    try:
        if not db.connect():
            raise HTTPException(status_code=503, detail="Database connection failed")
        
        query = """
            SELECT TransactionId, CustomerId, FromAccountNo, ToAccountNo,
                   Amount, TransferType, Decision, RiskScore, Reasons, CreatedAt
            FROM APITransactionLogs
            WHERE UserAction = 'PENDING'
            ORDER BY CreatedAt DESC
        """
        
        df = db.execute_query(query)
        
        transactions = []
        for _, row in df.iterrows():
            try:
                amount = float(row['Amount'])
                if pd.isna(amount) or np.isinf(amount):
                    amount = 0.0
            except:
                amount = 0.0
            
            try:
                risk_score = float(row['RiskScore'])
                if pd.isna(risk_score) or np.isinf(risk_score):
                    risk_score = 0.0
            except:
                risk_score = 0.0
            
            transactions.append({
                "transaction_id": str(row['TransactionId']),
                "customer_id": str(row['CustomerId']),
                "from_account": str(row['FromAccountNo']),
                "to_account": str(row['ToAccountNo']),
                "amount": amount,
                "transfer_type": str(row['TransferType']),
                "decision": str(row['Decision']),
                "risk_score": risk_score,
                "reasons": str(row['Reasons']),
                "timestamp": str(row['CreatedAt'])
            })
        
        return {"count": len(transactions), "transactions": transactions}
        
    except Exception as e:
        logger.error(f"Error fetching pending transactions: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        db.disconnect()
