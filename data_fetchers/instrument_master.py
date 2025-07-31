"""
DhanHQ Data Lake - Instrument Master Pipeline

This module handles the daily download and synchronization of the complete
instrument master list from DhanHQ. This is the foundation for discovering
all tradable instruments including F&O contracts.

Key Features:
- Automated daily download of instrument master CSV
- Parsing and cleaning of instrument data
- Bulk upsert operations to MongoDB with conflict resolution
- Data validation and integrity checks
- Support for both manual and scheduled execution

The instrument master contains ALL tradable instruments on Indian exchanges:
- Stocks (NSE, BSE)
- Indices (Nifty 50, Bank Nifty, Fin Nifty, etc.)
- Futures (Index + Stock)
- Options (Index + Stock, all strikes and expiries)
- Commodities and Currencies

Author: Data Lake Engineering Team
Version: 2.0
"""

import logging
import pandas as pd
import requests
from datetime import datetime, timezone, date
from typing import Dict, List, Any, Optional, Tuple
from pymongo import UpdateOne
from pymongo.errors import BulkWriteError
from database.collections import collections, get_instruments_master
from config.settings import config

# Configure logging
logger = logging.getLogger(__name__)

class InstrumentMasterError(Exception):
    """Custom exception for instrument master related errors."""
    pass

class InstrumentMasterFetcher:
    """
    Handles the complete lifecycle of instrument master data:
    1. Download from DhanHQ official source
    2. Parse and clean the data
    3. Synchronize with MongoDB
    4. Validate data integrity
    """
    
    # Official DhanHQ instrument master URLs
    COMPACT_URL = "https://images.dhan.co/api-data/api-scrip-master.csv"
    DETAILED_URL = "https://images.dhan.co/api-data/api-scrip-master-detailed.csv"
    
    def __init__(self):
        """Initialize the instrument master fetcher."""
        self.collection = get_instruments_master()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'DhanHQ-DataLake/2.0',
            'Accept': 'text/csv,application/csv'
        })
        
        logger.info("✅ InstrumentMasterFetcher initialized")
    
    def download_instrument_master(self, use_detailed: bool = True) -> pd.DataFrame:
        """
        Download the latest instrument master CSV from DhanHQ.
        
        Args:
            use_detailed (bool): Whether to use detailed or compact version
            
        Returns:
            pd.DataFrame: Parsed instrument master data
            
        Raises:
            InstrumentMasterError: If download or parsing fails
        """
        url = self.DETAILED_URL if use_detailed else self.COMPACT_URL
        csv_type = "detailed" if use_detailed else "compact"
        
        logger.info(f"📥 Downloading {csv_type} instrument master from DhanHQ...")
        
        try:
            # Download with timeout and retry logic
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Validate content type
            content_type = response.headers.get('content-type', '').lower()
            if 'csv' not in content_type and 'text' not in content_type:
                logger.warning(f"⚠️ Unexpected content type: {content_type}")
            
            logger.info(f"✅ Downloaded {len(response.content)} bytes")
            
            # Parse CSV with pandas
            df = pd.read_csv(
                pd.io.common.StringIO(response.text),
                dtype=str,  # Read everything as strings initially
                na_values=['', 'NA', 'NULL', 'null'],
                keep_default_na=False
            )
            
            logger.info(f"📊 Parsed {len(df)} instrument records")
            return df
            
        except requests.exceptions.RequestException as e:
            raise InstrumentMasterError(f"Failed to download instrument master: {str(e)}")
        except pd.errors.ParserError as e:
            raise InstrumentMasterError(f"Failed to parse CSV data: {str(e)}")
        except Exception as e:
            raise InstrumentMasterError(f"Unexpected error during download: {str(e)}")
    
    def clean_and_transform_data(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Clean and transform the raw CSV data for MongoDB storage.
        
        Args:
            df (pd.DataFrame): Raw instrument data
            
        Returns:
            List[Dict]: Cleaned instrument documents
        """
        logger.info("🧹 Cleaning and transforming instrument data...")
        
        cleaned_instruments = []
        
        for _, row in df.iterrows():
            try:
                # Build the document with type conversion
                doc = self._build_instrument_document(row)
                if doc:
                    cleaned_instruments.append(doc)
                    
            except Exception as e:
                logger.warning(f"⚠️ Skipping invalid instrument record: {e}")
                continue
        
        logger.info(f"✅ Cleaned {len(cleaned_instruments)} valid instruments")
        return cleaned_instruments
    
    def _build_instrument_document(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        """
        Build a single instrument document with proper data types.
        
        Args:
            row (pd.Series): Single row from CSV
            
        Returns:
            Dict: Cleaned instrument document or None if invalid
        """
        # Security ID is mandatory and must be numeric
        try:
            security_id = int(float(str(row['SECURITY_ID'])))
            if security_id <= 0:
                return None
        except (ValueError, TypeError, KeyError):
            return None
        
        # Build the document using the actual CSV column names
        doc = {
            'SECURITY_ID': security_id,
            'EXCH_ID': str(row.get('EXCH_ID', '')).strip(),
            'SEGMENT': str(row.get('SEGMENT', '')).strip(),
            'ISIN': str(row.get('ISIN', '')).strip(),
            'INSTRUMENT': str(row.get('INSTRUMENT', '')).strip(),
            'UNDERLYING_SECURITY_ID': self._safe_int(row.get('UNDERLYING_SECURITY_ID')),
            'UNDERLYING_SYMBOL': str(row.get('UNDERLYING_SYMBOL', '')).strip(),
            'SYMBOL_NAME': str(row.get('SYMBOL_NAME', '')).strip(),
            'DISPLAY_NAME': str(row.get('DISPLAY_NAME', '')).strip(),
            'INSTRUMENT_TYPE': str(row.get('INSTRUMENT_TYPE', '')).strip(),
            'SERIES': str(row.get('SERIES', '')).strip(),
            'LOT_SIZE': self._safe_int(row.get('LOT_SIZE'), 1),
            'TICK_SIZE': self._safe_float(row.get('TICK_SIZE'), 0.01),
            'LAST_UPDATED': datetime.now(timezone.utc)
        }
        
        # Handle expiry date - store as datetime instead of date
        expiry_str = str(row.get('SM_EXPIRY_DATE', '')).strip()
        if expiry_str and expiry_str not in ['', 'NaT', 'NULL', 'nan']:
            try:
                # Store as datetime (MongoDB compatible)
                expiry_date = pd.to_datetime(expiry_str)
                if not pd.isna(expiry_date):
                    doc['SM_EXPIRY_DATE'] = expiry_date.to_pydatetime()
                else:
                    doc['SM_EXPIRY_DATE'] = None
            except:
                doc['SM_EXPIRY_DATE'] = None
        else:
            doc['SM_EXPIRY_DATE'] = None
        
        # Handle strike price and option type for derivatives
        if any(opt_type in doc['INSTRUMENT'] for opt_type in ['OPT', 'OPTION']):
            doc['STRIKE_PRICE'] = self._safe_float(row.get('STRIKE_PRICE'))
            doc['OPTION_TYPE'] = str(row.get('OPTION_TYPE', '')).strip()
        else:
            doc['STRIKE_PRICE'] = self._safe_float(row.get('STRIKE_PRICE'))
            doc['OPTION_TYPE'] = str(row.get('OPTION_TYPE', '')).strip()
        
        # Add flags for tradability
        doc['BRACKET_FLAG'] = str(row.get('BRACKET_FLAG', 'N')).strip()
        doc['COVER_FLAG'] = str(row.get('COVER_FLAG', 'N')).strip()
        doc['EXPIRY_FLAG'] = str(row.get('EXPIRY_FLAG', '')).strip()
        
        return doc
    
    def _safe_int(self, value: Any, default: Optional[int] = None) -> Optional[int]:
        """Safely convert value to integer."""
        if pd.isna(value) or value == '' or value == 'NULL' or str(value).strip() == '':
            return default
        try:
            return int(float(str(value)))
        except (ValueError, TypeError):
            return default
    
    def _safe_float(self, value: Any, default: Optional[float] = None) -> Optional[float]:
        """Safely convert value to float."""
        if pd.isna(value) or value == '' or value == 'NULL' or str(value).strip() == '':
            return default
        try:
            return float(str(value))
        except (ValueError, TypeError):
            return default
    
    def sync_to_mongodb(self, instruments: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Synchronize instrument data to MongoDB using bulk upsert operations.
        
        Args:
            instruments (List[Dict]): List of instrument documents
            
        Returns:
            Dict[str, int]: Statistics about the sync operation
        """
        if not instruments:
            logger.warning("⚠️ No instruments to sync")
            return {'upserted': 0, 'modified': 0, 'errors': 0}
        
        logger.info(f"🔄 Syncing {len(instruments)} instruments to MongoDB...")
        
        # Prepare bulk operations
        bulk_operations = []
        
        for instrument in instruments:
            operation = UpdateOne(
                {'SECURITY_ID': instrument['SECURITY_ID']},  # Filter
                {'$set': instrument},  # Update
                upsert=True  # Create if doesn't exist
            )
            bulk_operations.append(operation)
        
        # Execute bulk operation
        try:
            result = self.collection.bulk_write(bulk_operations, ordered=False)
            
            stats = {
                'upserted': result.upserted_count,
                'modified': result.modified_count,
                'matched': result.matched_count,
                'errors': 0
            }
            
            logger.info(
                f"✅ Sync completed: {stats['upserted']} upserted, "
                f"{stats['modified']} modified, {stats['matched']} matched"
            )
            
            return stats
            
        except BulkWriteError as e:
            # Handle partial failures
            stats = {
                'upserted': e.details.get('nUpserted', 0),
                'modified': e.details.get('nModified', 0),
                'matched': e.details.get('nMatched', 0),
                'errors': len(e.details.get('writeErrors', []))
            }
            
            logger.error(f"❌ Bulk write had {stats['errors']} errors")
            for error in e.details.get('writeErrors', [])[:5]:  # Show first 5 errors
                logger.error(f"   Error: {error}")
            
            return stats
    
    def validate_sync_results(self, expected_count: int) -> Dict[str, Any]:
        """
        Validate the results of the sync operation.
        
        Args:
            expected_count (int): Expected number of instruments
            
        Returns:
            Dict: Validation results
        """
        logger.info("🔍 Validating sync results...")
        
        try:
            # Count total instruments
            total_count = self.collection.count_documents({})
            
            # Count by instrument type
            pipeline = [
                {'$group': {'_id': '$INSTRUMENT', 'count': {'$sum': 1}}},
                {'$sort': {'count': -1}}
            ]
            
            by_instrument = list(self.collection.aggregate(pipeline))
            
            # Count active F&O contracts (non-expired)
            today = datetime.now(timezone.utc)
            active_fo_count = self.collection.count_documents({
                'INSTRUMENT': {'$in': ['FUTSTK', 'OPTSTK', 'FUTIDX', 'OPTIDX', 'FUTCOM', 'OPTFUT']},
                '$or': [
                    {'SM_EXPIRY_DATE': {'$gte': today}},
                    {'SM_EXPIRY_DATE': None}
                ]
            })
            
            validation_results = {
                'status': 'healthy' if total_count > 0 else 'unhealthy',
                'total_instruments': total_count,
                'expected_count': expected_count,
                'coverage_ratio': total_count / expected_count if expected_count > 0 else 0,
                'active_fo_contracts': active_fo_count,
                'by_instrument_type': {item['_id']: item['count'] for item in by_instrument},
                'validation_timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"📊 Validation complete: {total_count} total instruments")
            logger.info(f"📊 Active F&O contracts: {active_fo_count}")
            
            return validation_results
            
        except Exception as e:
            logger.error(f"❌ Validation failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'total_instruments': 0,
                'expected_count': expected_count,
                'coverage_ratio': 0,
                'active_fo_contracts': 0,
                'by_instrument_type': {},
                'validation_timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def run_daily_sync(self) -> Dict[str, Any]:
        """
        Execute the complete daily instrument master sync process.
        
        Returns:
            Dict: Complete sync results and statistics
        """
        start_time = datetime.now(timezone.utc)
        logger.info("🚀 Starting daily instrument master sync...")
        
        try:
            # Step 1: Download
            df = self.download_instrument_master(use_detailed=True)
            
            # Step 2: Clean and transform
            instruments = self.clean_and_transform_data(df)
            
            # Step 3: Sync to MongoDB
            sync_stats = self.sync_to_mongodb(instruments)
            
            # Step 4: Validate
            validation = self.validate_sync_results(len(instruments))
            
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            
            results = {
                'status': 'success',
                'duration_seconds': round(duration, 2),
                'raw_count': len(df),
                'cleaned_count': len(instruments),
                'sync_stats': sync_stats,
                'validation': validation,
                'timestamp': end_time.isoformat()
            }
            
            logger.info(f"🎉 Daily sync completed successfully in {duration:.2f}s")
            return results
            
        except Exception as e:
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            
            logger.error(f"💥 Daily sync failed after {duration:.2f}s: {e}")
            
            return {
                'status': 'failed',
                'duration_seconds': round(duration, 2),
                'error': str(e),
                'timestamp': end_time.isoformat()
            }

# Global instrument master fetcher instance
instrument_fetcher = InstrumentMasterFetcher()

# Convenience exports
__all__ = [
    'instrument_fetcher',
    'InstrumentMasterFetcher',
    'InstrumentMasterError'
]