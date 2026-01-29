import pandas as pd
import logging
import csv
import os
from datetime import datetime
from api.models import TransactionRequest
from typing import List

logger = logging.getLogger(__name__)


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
                'PENDING',
                '',
                '',
                ''
            ])
        
        logger.info(f"Transaction {transaction_id} saved to {file_path}")
    except Exception as e:
        logger.error(f"Failed to save transaction to file: {e}")


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
