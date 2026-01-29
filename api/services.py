import pandas as pd
import numpy as np
import logging
import os
from datetime import datetime, timedelta
from typing import Dict
from fastapi import HTTPException

logger = logging.getLogger(__name__)


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
