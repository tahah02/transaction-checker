import pyodbc
import pandas as pd
import logging
import os
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        self.server = os.getenv("DB_SERVER")
        self.port = os.getenv("DB_PORT")
        self.database = os.getenv("DB_DATABASE")
        self.username = os.getenv("DB_USERNAME")
        self.password = os.getenv("DB_PASSWORD")
        self.connection = None
        
        self.REQUIRED_COLUMNS = [
            'CustomerId', 'TransferType', 'FromAccountCurrency', 'FromAccountNo',
            'SwiftCode', 'ReceipentAccount', 'ReceipentName', 'Amount', 'Currency',
            'PurposeCode', 'Charges', 'Status', 'CreateDate', 'FlagAmount',
            'FlagCurrency', 'AmountInAed', 'BankStatus', 'BankName', 'PurposeDetails',
            'ChargesAmount', 'BenId', 'AccountType', 'BankCountry', 'ChannelId'
        ]
    
    def connect(self) -> bool:
        try:
            if self.connection:
                self.disconnect()
            
            connection_string = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={self.server},{self.port};"
                f"DATABASE={self.database};"
                f"UID={self.username};"
                f"PWD={self.password};"
                f"Connection Timeout=15;"
                f"TrustServerCertificate=yes;"
                f"Encrypt=no;"
            )
            
            self.connection = pyodbc.connect(connection_string, timeout=15)
            
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.connection = None
            return False
    
    def disconnect(self):
        try:
            if self.connection:
                self.connection.close()
                self.connection = None
        except Exception as e:
            logger.error(f"Error closing connection: {e}")
    
    def is_connected(self) -> bool:
        try:
            if not self.connection:
                return False
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return True
        except:
            return False
    
    def execute_query(self, query: str, params: Optional[List] = None) -> pd.DataFrame:
        try:
            if not self.is_connected():
                if not self.connect():
                    raise Exception("Cannot connect to database")
            
            if params:
                return pd.read_sql(query, self.connection, params=params)
            else:
                return pd.read_sql(query, self.connection)
        except Exception as e:
            logger.error(f"Query error: {e}")
            raise
    
    def get_all_customers(self) -> List[str]:
        query = "SELECT DISTINCT CustomerId FROM TransactionHistoryLogs WHERE CustomerId IS NOT NULL ORDER BY CustomerId"
        df = self.execute_query(query)
        return df['CustomerId'].astype(str).tolist()
    
    def get_customer_accounts(self, customer_id: str) -> List[str]:
        query = "SELECT DISTINCT FromAccountNo FROM TransactionHistoryLogs WHERE CustomerId = ? AND FromAccountNo IS NOT NULL ORDER BY FromAccountNo"
        df = self.execute_query(query, [customer_id])
        return df['FromAccountNo'].astype(str).tolist()
    
    def get_account_transactions(self, customer_id: str, account_no: str) -> pd.DataFrame:
        columns_str = ", ".join([f"[{col}]" for col in self.REQUIRED_COLUMNS])
        query = f"SELECT {columns_str} FROM TransactionHistoryLogs WHERE CustomerId = ? AND FromAccountNo = ? ORDER BY CreateDate DESC"
        return self.execute_query(query, [customer_id, account_no])
    
    def get_customer_all_transactions(self, customer_id: str) -> pd.DataFrame:
        columns_str = ", ".join([f"[{col}]" for col in self.REQUIRED_COLUMNS])
        query = f"SELECT {columns_str} FROM TransactionHistoryLogs WHERE CustomerId = ? ORDER BY FromAccountNo, CreateDate DESC"
        return self.execute_query(query, [customer_id])
    
    def get_user_statistics(self, customer_id: str, account_no: str) -> Dict[str, Any]:
        try:
            df = self.get_account_transactions(customer_id, account_no)
            
            if len(df) == 0:
                return {
                    "user_avg_amount": 5000.0,
                    "user_std_amount": 2000.0,
                    "user_max_amount": 15000.0,
                    "user_txn_frequency": 0,
                    "user_international_ratio": 0.0,
                    "current_month_spending": 0.0
                }
            
            avg_amount = df['AmountInAed'].mean()
            std_amount = df['AmountInAed'].std() if len(df) > 1 else 2000.0
            max_amount = df['AmountInAed'].max()
            txn_count = len(df)
            
            intl_ratio = 0.0
            if 'TransferType' in df.columns:
                intl_count = len(df[df['TransferType'] == 'S'])
                intl_ratio = intl_count / txn_count if txn_count > 0 else 0.0
            
            current_month_spending = self.get_monthly_spending(customer_id, account_no)
            
            return {
                "user_avg_amount": float(avg_amount),
                "user_std_amount": float(std_amount),
                "user_max_amount": float(max_amount),
                "user_txn_frequency": int(txn_count),
                "user_international_ratio": float(intl_ratio),
                "current_month_spending": float(current_month_spending)
            }
        except Exception as e:
            logger.error(f"Error getting user statistics: {e}")
            return {
                "user_avg_amount": 5000.0,
                "user_std_amount": 2000.0,
                "user_max_amount": 15000.0,
                "user_txn_frequency": 0,
                "user_international_ratio": 0.0,
                "current_month_spending": 0.0
            }
    
    def get_monthly_spending(self, customer_id: str, account_no: str) -> float:
        try:
            query = """
                SELECT SUM(AmountInAed) as monthly_total
                FROM TransactionHistoryLogs 
                WHERE CustomerId = ? AND FromAccountNo = ? 
                AND MONTH(CreateDate) = MONTH(GETDATE()) 
                AND YEAR(CreateDate) = YEAR(GETDATE())
            """
            df = self.execute_query(query, [customer_id, account_no])
            return float(df['monthly_total'].iloc[0] or 0.0)
        except Exception as e:
            logger.error(f"Error getting monthly spending: {e}")
            return 0.0
    
    def check_new_beneficiary(self, customer_id: str, recipient_account: str) -> int:
        try:
            query = "SELECT COUNT(*) as count FROM TransactionHistoryLogs WHERE CustomerId = ? AND ReceipentAccount = ?"
            df = self.execute_query(query, [customer_id, recipient_account])
            return 0 if df['count'].iloc[0] > 0 else 1
        except Exception as e:
            logger.error(f"Error checking beneficiary: {e}")
            return 1
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

db_service = DatabaseService()

def get_db_service() -> DatabaseService:
    return db_service

if __name__ == "__main__":
    print("Testing Database Connection...")
    
    with DatabaseService() as db:
        if db.connect():
            print("✅ Connection successful!")
            
            customers = db.get_all_customers()[:5]
            print(f"Sample customers: {customers}")
            
            if customers:
                accounts = db.get_customer_accounts(customers[0])
                print(f"Customer {customers[0]} accounts: {accounts}")
                
                if accounts:
                    stats = db.get_user_statistics(customers[0], accounts[0])
                    print(f"Account stats: {stats}")
        else:
            print("❌ Connection failed!")