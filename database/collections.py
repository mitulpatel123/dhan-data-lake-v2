"""
DhanHQ Data Lake - Time-Series Collection Manager

This module handles the creation, indexing, and management of MongoDB
time-series collections optimized for financial market data storage.

Key Features:
- Automated time-series collection creation with optimal settings
- Strategic indexing for high-performance queries
- Collection validation and health monitoring
- Schema enforcement for data integrity
- Optimized storage for OHLCV and tick data

Collections Created:
1. instruments_master - Master list of all tradable instruments
2. historical_ohlcv - Time-series for historical OHLC+Volume data
3. live_tick_data - Time-series for real-time market ticks
4. option_chains - Option chain data with Greeks

Author: Data Lake Engineering Team
Version: 2.0
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from pymongo import ASCENDING, DESCENDING, TEXT
from pymongo.errors import CollectionInvalid, OperationFailure
from pymongo.collection import Collection
from database.mongodb_handler import mongodb

# Configure logging
logger = logging.getLogger(__name__)

class CollectionSetupError(Exception):
    """Custom exception for collection setup errors."""
    pass

class TimeSeriesCollectionManager:
    """
    Manages the creation and maintenance of MongoDB time-series collections
    optimized for financial market data ingestion and querying.
    """
    
    def __init__(self):
        """Initialize the collection manager."""
        self.db = mongodb.database
        self.client = mongodb.client
        
        # Collection configurations
        self.collection_configs = {
            'instruments_master': {
                'type': 'standard',
                'description': 'Master list of all tradable instruments',
                'indexes': [
                    {'keys': [('SECURITY_ID', ASCENDING)], 'unique': True, 'name': 'security_id_unique'},
                    {'keys': [('UNDERLYING_SYMBOL', ASCENDING)], 'name': 'underlying_symbol_idx'},
                    {'keys': [('INSTRUMENT', ASCENDING)], 'name': 'instrument_type_idx'},
                    {'keys': [('SM_EXPIRY_DATE', ASCENDING)], 'name': 'expiry_date_idx'},
                    {'keys': [('INSTRUMENT', ASCENDING), ('SM_EXPIRY_DATE', ASCENDING)], 'name': 'instrument_expiry_compound_idx'},
                    {'keys': [('DISPLAY_NAME', TEXT)], 'name': 'display_name_text_idx'}
                ]
            },
            'historical_ohlcv': {
                'type': 'timeseries',
                'time_field': 'timestamp',
                'meta_field': 'metadata',
                'granularity': 'minutes',
                'description': 'Historical OHLC+Volume time-series data',
                'indexes': [
                    {'keys': [('metadata.security_id', ASCENDING), ('timestamp', DESCENDING)], 'name': 'security_time_desc_idx'},
                    {'keys': [('metadata.symbol', ASCENDING)], 'name': 'symbol_idx'},
                    {'keys': [('metadata.instrument_type', ASCENDING)], 'name': 'instrument_type_idx'}
                ]
            },
            'live_tick_data': {
                'type': 'timeseries',
                'time_field': 'exchange_timestamp',
                'meta_field': 'metadata',
                'granularity': 'seconds',
                'description': 'Real-time market tick data',
                'indexes': [
                    {'keys': [('metadata.security_id', ASCENDING), ('exchange_timestamp', DESCENDING)], 'name': 'security_tick_time_idx'},
                    {'keys': [('exchange_timestamp', DESCENDING)], 'name': 'recent_ticks_idx'}
                ]
            },
            'option_chains': {
                'type': 'standard',
                'description': 'Option chain data with Greeks and OI',
                'indexes': [
                    {'keys': [('underlying_security_id', ASCENDING), ('expiry_date', ASCENDING), ('strike_price', ASCENDING), ('option_type', ASCENDING)], 'name': 'option_chain_compound_idx'},
                    {'keys': [('underlying_security_id', ASCENDING), ('timestamp', DESCENDING)], 'name': 'underlying_time_idx'},
                    {'keys': [('timestamp', DESCENDING)], 'name': 'recent_chains_idx'}
                ]
            }
        }
        
        logger.info("✅ TimeSeriesCollectionManager initialized")
    
    def create_collection(self, collection_name: str, force_recreate: bool = False) -> bool:
        """
        Create a single collection with its optimal configuration.
        
        Args:
            collection_name (str): Name of the collection to create
            force_recreate (bool): Whether to drop and recreate if exists
            
        Returns:
            bool: True if created successfully, False if already exists
            
        Raises:
            CollectionSetupError: If collection creation fails
        """
        if collection_name not in self.collection_configs:
            raise CollectionSetupError(f"Unknown collection: {collection_name}")
        
        config = self.collection_configs[collection_name]
        
        try:
            # Check if collection already exists
            existing_collections = self.db.list_collection_names()
            
            if collection_name in existing_collections:
                if force_recreate:
                    logger.info(f"🗑️ Dropping existing collection: {collection_name}")
                    self.db.drop_collection(collection_name)
                else:
                    logger.info(f"⚠️ Collection '{collection_name}' already exists, skipping creation")
                    return False
            
            # Create collection based on type
            if config['type'] == 'timeseries':
                self._create_timeseries_collection(collection_name, config)
            else:
                self._create_standard_collection(collection_name, config)
            
            # Create indexes
            self._create_indexes(collection_name, config.get('indexes', []))
            
            logger.info(f"✅ Collection '{collection_name}' created successfully")
            return True
            
        except Exception as e:
            raise CollectionSetupError(f"Failed to create collection '{collection_name}': {str(e)}")
    
    def _create_timeseries_collection(self, collection_name: str, config: Dict[str, Any]) -> None:
        """Create a time-series collection with optimal settings."""
        timeseries_options = {
            'timeField': config['time_field'],
            'metaField': config['meta_field'],
            'granularity': config['granularity']
        }
        
        # MongoDB 8.0+ doesn't allow bucketRoundingSeconds with granularity
        # The granularity parameter handles bucketing automatically
        
        self.db.create_collection(
            collection_name,
            timeseries=timeseries_options
        )
        
        logger.info(
            f"📊 Time-series collection '{collection_name}' created with "
            f"timeField='{config['time_field']}', granularity='{config['granularity']}'"
        )
    
    def _create_standard_collection(self, collection_name: str, config: Dict[str, Any]) -> None:
        """Create a standard collection."""
        self.db.create_collection(collection_name)
        logger.info(f"📄 Standard collection '{collection_name}' created")
    
    def _create_indexes(self, collection_name: str, indexes: List[Dict[str, Any]]) -> None:
        """Create indexes for a collection."""
        if not indexes:
            return
        
        collection = self.db[collection_name]
        
        for index_config in indexes:
            try:
                keys = index_config['keys']
                options = {k: v for k, v in index_config.items() if k != 'keys'}
                
                collection.create_index(keys, **options)
                index_name = options.get('name', 'unnamed_index')
                logger.info(f"📍 Index '{index_name}' created on '{collection_name}'")
                
            except OperationFailure as e:
                if "already exists" in str(e):
                    logger.info(f"⚠️ Index already exists: {index_config.get('name', 'unnamed')}")
                else:
                    raise CollectionSetupError(f"Failed to create index: {str(e)}")
    
    def create_all_collections(self, force_recreate: bool = False) -> Dict[str, bool]:
        """
        Create all required collections for the data lake.
        
        Args:
            force_recreate (bool): Whether to drop and recreate existing collections
            
        Returns:
            Dict[str, bool]: Status of each collection creation
        """
        results = {}
        
        logger.info("🏗️ Creating all collections for DhanHQ Data Lake...")
        
        for collection_name in self.collection_configs.keys():
            try:
                results[collection_name] = self.create_collection(collection_name, force_recreate)
            except CollectionSetupError as e:
                logger.error(f"❌ Failed to create '{collection_name}': {e}")
                results[collection_name] = False
        
        successful = sum(1 for v in results.values() if v)
        total = len(results)
        
        logger.info(f"✅ Collection creation completed: {successful}/{total} successful")
        return results
    
    def validate_collections(self) -> Dict[str, Any]:
        """
        Validate that all required collections exist with proper configuration.
        
        Returns:
            Dict containing validation results
        """
        validation_results = {
            'status': 'healthy',
            'collections': {},
            'missing_collections': [],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        existing_collections = self.db.list_collection_names()
        
        for collection_name, config in self.collection_configs.items():
            if collection_name not in existing_collections:
                validation_results['missing_collections'].append(collection_name)
                validation_results['status'] = 'unhealthy'
                continue
            
            # Validate collection
            collection_info = self._validate_single_collection(collection_name, config)
            validation_results['collections'][collection_name] = collection_info
        
        return validation_results
    
    def _validate_single_collection(self, collection_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single collection's configuration."""
        collection = self.db[collection_name]
        
        try:
            # Get collection stats
            stats = self.db.command('collStats', collection_name)
            
            # Get index information
            indexes = list(collection.list_indexes())
            
            # Check if it's a time-series collection
            is_timeseries = 'timeseries' in stats
            
            return {
                'exists': True,
                'type': 'timeseries' if is_timeseries else 'standard',
                'document_count': stats.get('count', 0),
                'size_mb': round(stats.get('size', 0) / (1024*1024), 2),
                'index_count': len(indexes),
                'indexes': [idx['name'] for idx in indexes],
                'timeseries_config': stats.get('timeseries') if is_timeseries else None
            }
            
        except Exception as e:
            logger.error(f"❌ Error validating collection '{collection_name}': {e}")
            return {
                'exists': True,
                'error': str(e)
            }
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics for all collections."""
        stats = {
            'database_name': self.db.name,
            'total_collections': 0,
            'total_documents': 0,
            'total_size_mb': 0,
            'collections': {},
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        try:
            for collection_name in self.collection_configs.keys():
                if collection_name in self.db.list_collection_names():
                    collection_stats = self.db.command('collStats', collection_name)
                    
                    stats['collections'][collection_name] = {
                        'documents': collection_stats.get('count', 0),
                        'size_mb': round(collection_stats.get('size', 0) / (1024*1024), 2),
                        'avg_obj_size': collection_stats.get('avgObjSize', 0),
                        'indexes': collection_stats.get('nindexes', 0)
                    }
                    
                    stats['total_documents'] += collection_stats.get('count', 0)
                    stats['total_size_mb'] += round(collection_stats.get('size', 0) / (1024*1024), 2)
                    stats['total_collections'] += 1
            
        except Exception as e:
            logger.error(f"❌ Error getting collection stats: {e}")
            stats['error'] = str(e)
        
        return stats
    
    def get_collection(self, collection_name: str) -> Collection:
        """
        Get a reference to a specific collection.
        
        Args:
            collection_name (str): Name of the collection
            
        Returns:
            Collection: MongoDB collection reference
            
        Raises:
            CollectionSetupError: If collection doesn't exist
        """
        if collection_name not in self.collection_configs:
            raise CollectionSetupError(f"Unknown collection: {collection_name}")
        
        if collection_name not in self.db.list_collection_names():
            raise CollectionSetupError(f"Collection '{collection_name}' does not exist. Run create_all_collections() first.")
        
        return self.db[collection_name]

# Global collection manager instance
try:
    collections = TimeSeriesCollectionManager()
    logger.info("🚀 Global TimeSeriesCollectionManager instance created")
except Exception as e:
    logger.error(f"💥 Failed to create TimeSeriesCollectionManager: {e}")
    raise

# Convenience exports for easy importing
__all__ = [
    'collections',
    'TimeSeriesCollectionManager',
    'CollectionSetupError'
]

# Quick access to collection references (created on-demand)
def get_instruments_master() -> Collection:
    """Get instruments_master collection reference."""
    return collections.get_collection('instruments_master')

def get_historical_ohlcv() -> Collection:
    """Get historical_ohlcv collection reference."""
    return collections.get_collection('historical_ohlcv')

def get_live_tick_data() -> Collection:
    """Get live_tick_data collection reference."""
    return collections.get_collection('live_tick_data')

def get_option_chains() -> Collection:
    """Get option_chains collection reference."""
    return collections.get_collection('option_chains')