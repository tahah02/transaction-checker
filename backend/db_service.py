import pandas as pd
import logging
import os
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any


try:
    import pyodbc
    DRIVER_TYPE = 'pyodbc'
    logger = logging.getLogger(__name__)
    logger.info("Using pyodbc driver")
except ImportError:
    try:
        import pymssql
        DRIVER_TYPE = 'pymssql'
        logger = logging.getLogger(__name__)
        logger.info("Using pymssql driver")
    except ImportError:
        raise ImportError("Neither pymssql nor pyodbc is installed. Please install one of them.")

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        self.server = os.getenv("DB_SERVER", "localhost")
        self.port = int(os.getenv("DB_PORT", "1433"))
        self.database = os.getenv("DB_DATABASE", "retailchannelLogs")
        self.username = os.getenv("DB_USERNAME", "dbuser")
        self.password = os.getenv("DB_PASSWORD", "")
        self.connection = None
        self.connection_pool = []
        self.pool_size = 5
        
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
                return True
            
            if DRIVER_TYPE == 'pyodbc':
                conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={self.server},{self.port};DATABASE={self.database};UID={self.username};PWD={self.password}"
                self.connection = pyodbc.connect(conn_str, timeout=15)
                logger.info("Connected using pyodbc")
            else:
                self.connection = pymssql.connect(
                    server=self.server,
                    port=self.port,
                    database=self.database,
                    user=self.username,
                    password=self.password,
                    timeout=15,
                    login_timeout=15
                )
                logger.info("Connected using pymssql with connection pooling")
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
            
            cursor = self.connection.cursor()
            
            if params:
                cursor.execute(query, tuple(params))
            else:
                cursor.execute(query)
            
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            cursor.close()
            
            df = pd.DataFrame.from_records(rows, columns=columns)
            
            for col in df.columns:
                if df[col].dtype == 'object':
                    try:
                        df[col] = pd.to_numeric(df[col], errors='ignore')
                    except:
                        pass
            
            return df
        except Exception as e:
            logger.error(f"Query error: {e}")
            raise
    
    def execute_non_query(self, query: str, params: Optional[List] = None) -> int:
        try:
            if not self.is_connected():
                if not self.connect():
                    raise Exception("Cannot connect to database")
            
            cursor = self.connection.cursor()
            
            if params:
                cursor.execute(query, tuple(params))
            else:
                cursor.execute(query)
            
            self.connection.commit()
            rows_affected = cursor.rowcount
            cursor.close()
            
            return rows_affected
        except Exception as e:
            logger.error(f"Non-query error: {e}")
            if self.connection:
                self.connection.rollback()
            raise
    
    def get_all_customers(self) -> List[str]:
        query = "SELECT DISTINCT CustomerId FROM TransactionHistoryLogs WHERE CustomerId IS NOT NULL ORDER BY CustomerId"
        df = self.execute_query(query)
        return df['CustomerId'].astype(str).tolist()
    
    def get_customer_accounts(self, customer_id: str) -> List[str]:
        if DRIVER_TYPE == 'pymssql':
            query = "SELECT DISTINCT FromAccountNo FROM TransactionHistoryLogs WHERE CustomerId = %s AND FromAccountNo IS NOT NULL ORDER BY FromAccountNo"
        else:
            query = "SELECT DISTINCT FromAccountNo FROM TransactionHistoryLogs WHERE CustomerId = ? AND FromAccountNo IS NOT NULL ORDER BY FromAccountNo"
        df = self.execute_query(query, [customer_id])
        return df['FromAccountNo'].astype(str).tolist()
    
    def get_account_transactions(self, customer_id: str, account_no: str) -> pd.DataFrame:
        columns_str = ", ".join([f"[{col}]" for col in self.REQUIRED_COLUMNS])
        # Try both with and without leading zeros
        padded_account = account_no.zfill(14)  # Pad to 14 digits
        if DRIVER_TYPE == 'pymssql':
            query = f"""SELECT {columns_str} FROM TransactionHistoryLogs 
                        WHERE CustomerId = %s 
                        AND (FromAccountNo = %s OR FromAccountNo = %s)
                        ORDER BY CreateDate DESC"""
        else:
            query = f"""SELECT {columns_str} FROM TransactionHistoryLogs 
                        WHERE CustomerId = ? 
                        AND (FromAccountNo = ? OR FromAccountNo = ?)
                        ORDER BY CreateDate DESC"""
        return self.execute_query(query, [customer_id, account_no, padded_account])
    
    def get_customer_all_transactions(self, customer_id: str) -> pd.DataFrame:
        columns_str = ", ".join([f"[{col}]" for col in self.REQUIRED_COLUMNS])
        if DRIVER_TYPE == 'pymssql':
            query = f"SELECT {columns_str} FROM TransactionHistoryLogs WHERE CustomerId = %s ORDER BY FromAccountNo, CreateDate DESC"
        else:
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
            
            avg_amount = float(df['AmountInAed'].mean())
            std_amount = float(df['AmountInAed'].std()) if len(df) > 1 else 2000.0
            max_amount = float(df['AmountInAed'].max())
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
            padded_account = account_no.zfill(14)
            if DRIVER_TYPE == 'pymssql':
                query = """
                    SELECT COALESCE(SUM(AmountInAed), 0) as monthly_total
                    FROM (
                        SELECT AmountInAed FROM TransactionHistoryLogs 
                        WHERE CustomerId = %s AND (FromAccountNo = %s OR FromAccountNo = %s)
                        AND CreateDate >= DATEADD(MONTH, DATEDIFF(MONTH, 0, GETDATE()), 0)
                        AND CreateDate < DATEADD(MONTH, DATEDIFF(MONTH, 0, GETDATE()) + 1, 0)
                        
                        UNION ALL
                        
                        SELECT AmountInAed FROM APITransactionLogs 
                        WHERE CustomerId = %s AND (FromAccountNo = %s OR FromAccountNo = %s)
                        AND CreateDate >= DATEADD(MONTH, DATEDIFF(MONTH, 0, GETDATE()), 0)
                        AND CreateDate < DATEADD(MONTH, DATEDIFF(MONTH, 0, GETDATE()) + 1, 0)
                    ) combined
                """
                params = [customer_id, account_no, padded_account, customer_id, account_no, padded_account]
            else:
                query = """
                    SELECT COALESCE(SUM(AmountInAed), 0) as monthly_total
                    FROM (
                        SELECT AmountInAed FROM TransactionHistoryLogs 
                        WHERE CustomerId = ? AND (FromAccountNo = ? OR FromAccountNo = ?)
                        AND CreateDate >= DATEADD(MONTH, DATEDIFF(MONTH, 0, GETDATE()), 0)
                        AND CreateDate < DATEADD(MONTH, DATEDIFF(MONTH, 0, GETDATE()) + 1, 0)
                        
                        UNION ALL
                        
                        SELECT AmountInAed FROM APITransactionLogs 
                        WHERE CustomerId = ? AND (FromAccountNo = ? OR FromAccountNo = ?)
                        AND CreateDate >= DATEADD(MONTH, DATEDIFF(MONTH, 0, GETDATE()), 0)
                        AND CreateDate < DATEADD(MONTH, DATEDIFF(MONTH, 0, GETDATE()) + 1, 0)
                    ) combined
                """
                params = [customer_id, account_no, padded_account, customer_id, account_no, padded_account]
            df = self.execute_query(query, params)
            return float(df['monthly_total'].iloc[0] or 0.0)
        except Exception as e:
            logger.error(f"Error getting monthly spending: {e}")
            return 0.0
    
    def check_new_beneficiary(self, customer_id: str, recipient_account: str, transfer_type: str = None) -> int:
        try:
            placeholder = '%s' if DRIVER_TYPE == 'pymssql' else '?'
            
            if transfer_type:
                query = f"SELECT COUNT(*) as count FROM TransactionHistoryLogs WHERE CustomerId = {placeholder} AND ReceipentAccount = {placeholder} AND TransferType = {placeholder}"
                params = [customer_id, recipient_account, transfer_type]
            else:
                query = f"SELECT COUNT(*) as count FROM TransactionHistoryLogs WHERE CustomerId = {placeholder} AND ReceipentAccount = {placeholder}"
                params = [customer_id, recipient_account]
            
            df = self.execute_query(query, params)
            return 0 if df['count'].iloc[0] > 0 else 1
        except Exception as e:
            logger.error(f"Error checking beneficiary: {e}")
            return 1
    
    def get_weekly_stats(self, customer_id: str, account_no: str) -> Dict[str, Any]:
        try:
            padded_account = account_no.zfill(14)
            if DRIVER_TYPE == 'pymssql':
                query = """
                    SELECT 
                        SUM(AmountInAed) as weekly_total,
                        COUNT(*) as weekly_txn_count,
                        AVG(AmountInAed) as weekly_avg_amount,
                        STDEV(AmountInAed) as weekly_std
                    FROM TransactionHistoryLogs 
                    WHERE CustomerId = %s AND (FromAccountNo = %s OR FromAccountNo = %s)
                    AND CreateDate >= DATEADD(DAY, -7, CAST(GETDATE() AS DATE))
                """
            else:
                query = """
                    SELECT 
                        SUM(AmountInAed) as weekly_total,
                        COUNT(*) as weekly_txn_count,
                        AVG(AmountInAed) as weekly_avg_amount,
                        STDEV(AmountInAed) as weekly_std
                    FROM TransactionHistoryLogs 
                    WHERE CustomerId = ? AND (FromAccountNo = ? OR FromAccountNo = ?)
                    AND CreateDate >= DATEADD(DAY, -7, CAST(GETDATE() AS DATE))
                """
            df = self.execute_query(query, [customer_id, account_no, padded_account])
            
            weekly_total = float(df['weekly_total'].iloc[0] or 0.0)
            weekly_txn_count = int(df['weekly_txn_count'].iloc[0] or 0)
            weekly_avg = float(df['weekly_avg_amount'].iloc[0] or 0.0)
            weekly_std = float(df['weekly_std'].iloc[0] or 0.0) if df['weekly_std'].iloc[0] is not None else 0.0
            
            weekly_deviation = 0.0
            if weekly_avg > 0:
                if DRIVER_TYPE == 'pymssql':
                    query_deviation = """
                        SELECT AVG(ABS(AmountInAed - %s)) as avg_deviation
                        FROM TransactionHistoryLogs 
                        WHERE CustomerId = %s AND (FromAccountNo = %s OR FromAccountNo = %s)
                        AND CreateDate >= DATEADD(DAY, -7, CAST(GETDATE() AS DATE))
                    """
                else:
                    query_deviation = """
                        SELECT AVG(ABS(AmountInAed - ?)) as avg_deviation
                        FROM TransactionHistoryLogs 
                        WHERE CustomerId = ? AND (FromAccountNo = ? OR FromAccountNo = ?)
                        AND CreateDate >= DATEADD(DAY, -7, CAST(GETDATE() AS DATE))
                    """
                df_dev = self.execute_query(query_deviation, [weekly_avg, customer_id, account_no, padded_account])
                weekly_deviation = float(df_dev['avg_deviation'].iloc[0] or 0.0) if df_dev['avg_deviation'].iloc[0] is not None else 0.0
            
            return {
                "user_weekly_total": weekly_total,
                "user_weekly_txn_count": weekly_txn_count,
                "user_weekly_avg_amount": weekly_avg,
                "user_weekly_deviation": weekly_deviation
            }
        except Exception as e:
            logger.error(f"Error getting weekly stats: {e}")
            return {
                "user_weekly_total": 0.0,
                "user_weekly_txn_count": 0,
                "user_weekly_avg_amount": 0.0,
                "user_weekly_deviation": 0.0
            }
    
    def get_monthly_stats(self, customer_id: str, account_no: str) -> Dict[str, Any]:
        try:
            padded_account = account_no.zfill(14)
            if DRIVER_TYPE == 'pymssql':
                query = """
                    SELECT 
                        SUM(AmountInAed) as monthly_total,
                        COUNT(*) as monthly_txn_count,
                        AVG(AmountInAed) as monthly_avg_amount
                    FROM TransactionHistoryLogs 
                    WHERE CustomerId = %s AND (FromAccountNo = %s OR FromAccountNo = %s)
                    AND MONTH(CreateDate) = MONTH(GETDATE()) 
                    AND YEAR(CreateDate) = YEAR(GETDATE())
                """
            else:
                query = """
                    SELECT 
                        SUM(AmountInAed) as monthly_total,
                        COUNT(*) as monthly_txn_count,
                        AVG(AmountInAed) as monthly_avg_amount
                    FROM TransactionHistoryLogs 
                    WHERE CustomerId = ? AND (FromAccountNo = ? OR FromAccountNo = ?)
                    AND MONTH(CreateDate) = MONTH(GETDATE()) 
                    AND YEAR(CreateDate) = YEAR(GETDATE())
                """
            df = self.execute_query(query, [customer_id, account_no, padded_account])
            
            monthly_total = float(df['monthly_total'].iloc[0] or 0.0)
            monthly_txn_count = int(df['monthly_txn_count'].iloc[0] or 0)
            monthly_avg = float(df['monthly_avg_amount'].iloc[0] or 0.0)
            
            monthly_deviation = 0.0
            if monthly_avg > 0:
                if DRIVER_TYPE == 'pymssql':
                    query_deviation = """
                        SELECT AVG(ABS(AmountInAed - %s)) as avg_deviation
                        FROM TransactionHistoryLogs 
                        WHERE CustomerId = %s AND (FromAccountNo = %s OR FromAccountNo = %s) 
                        AND MONTH(CreateDate) = MONTH(GETDATE()) 
                        AND YEAR(CreateDate) = YEAR(GETDATE())
                    """
                else:
                    query_deviation = """
                        SELECT AVG(ABS(AmountInAed - ?)) as avg_deviation
                        FROM TransactionHistoryLogs 
                        WHERE CustomerId = ? AND (FromAccountNo = ? OR FromAccountNo = ?) 
                        AND MONTH(CreateDate) = MONTH(GETDATE()) 
                        AND YEAR(CreateDate) = YEAR(GETDATE())
                    """
                df_dev = self.execute_query(query_deviation, [monthly_avg, customer_id, account_no, padded_account])
                monthly_deviation = float(df_dev['avg_deviation'].iloc[0] or 0.0) if df_dev['avg_deviation'].iloc[0] is not None else 0.0
            
            return {
                "current_month_spending": monthly_total,
                "user_monthly_txn_count": monthly_txn_count,
                "user_monthly_avg_amount": monthly_avg,
                "user_monthly_deviation": monthly_deviation
            }
        except Exception as e:
            logger.error(f"Error getting monthly stats: {e}")
            return {
                "current_month_spending": 0.0,
                "user_monthly_txn_count": 0,
                "user_monthly_avg_amount": 0.0,
                "user_monthly_deviation": 0.0
            }
    
    def get_velocity_metrics(self, customer_id: str, account_no: str) -> Dict[str, Any]:
        try:
            padded_account = account_no.zfill(14)
            if DRIVER_TYPE == 'pymssql':
                query = """
                    SELECT 
                        COUNT(CASE WHEN CreateDate >= DATEADD(MINUTE, -10, GETDATE()) THEN 1 END) as txn_count_10min,
                        COUNT(CASE WHEN CreateDate >= DATEADD(HOUR, -1, GETDATE()) THEN 1 END) as txn_count_1hour,
                        MAX(CreateDate) as last_txn_time
                    FROM TransactionHistoryLogs 
                    WHERE CustomerId = %s AND (FromAccountNo = %s OR FromAccountNo = %s)
                """
            else:
                query = """
                    SELECT 
                        COUNT(CASE WHEN CreateDate >= DATEADD(MINUTE, -10, GETDATE()) THEN 1 END) as txn_count_10min,
                        COUNT(CASE WHEN CreateDate >= DATEADD(HOUR, -1, GETDATE()) THEN 1 END) as txn_count_1hour,
                        MAX(CreateDate) as last_txn_time
                    FROM TransactionHistoryLogs 
                    WHERE CustomerId = ? AND (FromAccountNo = ? OR FromAccountNo = ?)
                """
            df = self.execute_query(query, [customer_id, account_no, padded_account])
            
            txn_count_10min = int(df['txn_count_10min'].iloc[0] or 0)
            txn_count_1hour = int(df['txn_count_1hour'].iloc[0] or 0)
            last_txn_time = df['last_txn_time'].iloc[0]
            
            time_since_last_txn = 3600.0
            if last_txn_time:
                from datetime import datetime
                time_diff = datetime.now() - last_txn_time
                time_since_last_txn = time_diff.total_seconds()
            
            return {
                "txn_count_10min": txn_count_10min,
                "txn_count_1hour": txn_count_1hour,
                "time_since_last_txn": time_since_last_txn
            }
        except Exception as e:
            logger.error(f"Error getting velocity metrics: {e}")
            return {
                "txn_count_10min": 0,
                "txn_count_1hour": 0,
                "time_since_last_txn": 3600.0
            }
    
    def get_all_user_stats(self, customer_id: str, account_no: str) -> Dict[str, Any]:
        try:
            base_stats = self.get_user_statistics(customer_id, account_no)
            weekly_stats = self.get_weekly_stats(customer_id, account_no)
            monthly_stats = self.get_monthly_stats(customer_id, account_no)
            velocity_stats = self.get_velocity_metrics(customer_id, account_no)
            
            combined_stats = {
                **base_stats,
                **weekly_stats,
                **monthly_stats,
                **velocity_stats
            }
            
            return combined_stats
        except Exception as e:
            logger.error(f"Error getting all user stats: {e}")
            return {
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
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def get_enabled_features(self) -> List[str]:
        try:
            if not self.is_connected():
                if not self.connect():
                    return []
            
            query = "SELECT FeatureName FROM FeaturesConfig WHERE IsEnabled = 1"
            result = self.execute_query(query)
            if result is not None and not result.empty:
                return result['FeatureName'].tolist()
            return []
        except Exception as e:
            logger.error(f"Error fetching enabled features: {e}")
            return []

    def insert_transaction_log(self, idempotence_key: str, request_method: str, 
                               request_endpoint: str, request_payload: str,
                               response_status_code: int, is_successful: bool,
                               user_id: str = None, client_ip: str = None,
                               response_payload: str = None, risk_score: float = None,
                               decision: str = None, error_code: str = None,
                               error_message: str = None, execution_time_ms: int = None) -> int:
        try:
            if not self.is_connected():
                if not self.connect():
                    return -1
            
            query = """
            INSERT INTO TransactionLogs (
                IdempotenceKey, RequestMethod, RequestEndpoint, RequestPayload,
                ResponseStatusCode, IsSuccessful, UserID, ClientIP, ResponsePayload,
                RiskScore, Decision, ErrorCode, ErrorMessage, ExecutionTimeMs, CreatedAt
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, GETDATE())
            """
            
            params = [
                idempotence_key, request_method, request_endpoint, request_payload,
                response_status_code, is_successful, user_id, client_ip, response_payload,
                risk_score, decision, error_code, error_message, execution_time_ms
            ]
            
            return self.execute_non_query(query, params)
        except Exception as e:
            logger.error(f"Error inserting transaction log: {e}")
            return -1

    def get_transaction_log_by_idempotence_key(self, idempotence_key: str) -> dict:
        try:
            if not self.is_connected():
                if not self.connect():
                    return None
            
            query = """
            SELECT * FROM TransactionLogs 
            WHERE IdempotenceKey = %s AND IsSuccessful = %s
            ORDER BY CreatedAt DESC
            """
            
            result = self.execute_query(query, [idempotence_key, 1])
            
            if result is not None and not result.empty:
                return result.iloc[0].to_dict()
            return None
        except Exception as e:
            logger.error(f"Error fetching transaction log: {e}")
            return None

    def get_customer_checks_config(self, customer_id: str, account_no: str, transfer_type: str) -> Dict[str, int]:
        try:
            if not self.is_connected():
                if not self.connect():
                    return self._default_checks_config()

            query = """
            SELECT ParameterName, IsEnabled
            FROM CustomerAccountTransferTypeConfig
            WHERE CustomerID = %s AND AccountNo = %s AND TransferType = %s
            AND ParameterName IN ('velocity_check_10min', 'velocity_check_1hour', 'monthly_spending_check', 'new_beneficiary_check')
            AND IsActive = 1
            """

            result = self.execute_query(query, [customer_id, account_no, transfer_type])

            config = self._default_checks_config()

            if result is not None and len(result) > 0:
                for _, row in result.iterrows():
                    param_name = row['ParameterName']
                    if param_name in config:
                        config[param_name] = row['IsEnabled']

            return config

        except Exception as e:
            logger.error(f"Error fetching customer checks config: {e}")
            return self._default_checks_config()

    def _default_checks_config(self) -> Dict[str, int]:
        return {
            'velocity_check_10min': 1,
            'velocity_check_1hour': 1,
            'monthly_spending_check': 1,
            'new_beneficiary_check': 1
        }

db_service = DatabaseService()

def get_db_service() -> DatabaseService:
    return db_service

if __name__ == "__main__":
    print("Testing Database Connection...")
    
    with DatabaseService() as db:
        if db.connect():
            print("Connection successful!")
            
            customers = db.get_all_customers()[:5]
            print(f"Sample customers: {customers}")
            
            if customers:
                accounts = db.get_customer_accounts(customers[0])
                print(f"Customer {customers[0]} accounts: {accounts}")
                
                if accounts:
                    stats = db.get_user_statistics(customers[0], accounts[0])
                    print(f"Account stats: {stats}")
        else:
            print("Connection failed!")
