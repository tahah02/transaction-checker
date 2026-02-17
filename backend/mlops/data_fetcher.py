import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Optional
from backend.db_service import get_db_service

logger = logging.getLogger(__name__)


class DataFetcher:
    def __init__(self):
        self.db = get_db_service()
    
    def fetch_historical_data(self) -> pd.DataFrame:
        try:
            logger.info("Fetching historical data from TransactionHistoryLogs...")
            query = "SELECT CustomerId, FromAccountNo, ReceipentAccount, AmountInAed, TransferType, CreateDate, ChannelId, BankCountry FROM TransactionHistoryLogs WHERE CreateDate IS NOT NULL ORDER BY CreateDate DESC"
            df = self.db.execute_query(query)
            logger.info(f"Fetched {len(df)} historical records")
            return df if df is not None else pd.DataFrame()
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return pd.DataFrame()
    
    def fetch_recent_data(self, since_date: Optional[datetime] = None) -> pd.DataFrame:
        try:
            if since_date is None:
                since_date = datetime.now() - timedelta(days=30)
            
            logger.info(f"Fetching recent data from APITransactionLogs since {since_date}...")
            query = "SELECT CustomerId, FromAccountNo, ReceipentAccount, AmountInAed, TransferType, CreatedAt as CreateDate, ChannelId, BankCountry, IsFraud FROM APITransactionLogs WHERE CreatedAt >= %s AND CreatedAt IS NOT NULL ORDER BY CreatedAt DESC"
            df = self.db.execute_query(query, [since_date])
            logger.info(f"Fetched {len(df)} recent records")
            return df if df is not None else pd.DataFrame()
        except Exception as e:
            logger.error(f"Error fetching recent data: {e}")
            return pd.DataFrame()
    
    def merge_datasets(self, historical: pd.DataFrame, recent: pd.DataFrame) -> pd.DataFrame:
        try:
            logger.info("Merging historical and recent datasets...")
            if historical.empty and recent.empty:
                return pd.DataFrame()
            
            combined = pd.concat([historical, recent], ignore_index=True)
            combined = combined.drop_duplicates(subset=['CustomerId', 'FromAccountNo', 'CreateDate'], keep='last')
            logger.info(f"Combined dataset size: {len(combined)} records")
            return combined
        except Exception as e:
            logger.error(f"Error merging datasets: {e}")
            return pd.DataFrame()
    
    def fetch_training_data(self, since_date: Optional[datetime] = None) -> pd.DataFrame:
        try:
            historical = self.fetch_historical_data()
            recent = self.fetch_recent_data(since_date)
            
            if historical.empty and recent.empty:
                logger.warning("No data fetched from database!")
                return pd.DataFrame()
            
            combined = self.merge_datasets(historical, recent)
            return combined
        except Exception as e:
            logger.error(f"Error in fetch_training_data: {e}")
            return pd.DataFrame()


def get_data_fetcher() -> DataFetcher:
    return DataFetcher()
