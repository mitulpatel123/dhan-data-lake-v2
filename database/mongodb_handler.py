"""
DhanHQ Data Lake - MongoDB Connection Manager

This module provides a robust, production-ready MongoDB connection manager
with connection pooling, error handling, and health monitoring capabilities.

Key Features:
- Singleton pattern for efficient connection management
- Connection pooling with configurable parameters
- Comprehensive error handling and retry logic
- Health checks and connection monitoring
- Support for both sync and async operations
- Time-series collection optimization

Author: Data Lake Engineering Team
Version: 2.0
"""

import logging
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import (
    ConnectionFailure, 
    ServerSelectionTimeoutError,
    OperationFailure,
    ConfigurationError as PyMongoConfigError
)
from pymongo.database import Database
from pymongo.collection import Collection
import motor.motor_asyncio
from config.settings import config

# Configure logging
logger = logging.getLogger(__name__)

class MongoDBConnectionError(Exception):
    """Custom exception for MongoDB connection-related errors."""
    pass

class MongoDBHandler:
    """
    Production-grade MongoDB connection manager with connection pooling,
    health monitoring, and optimized settings for financial time-series data.
    
    This class implements the singleton pattern to ensure efficient
    connection management across the entire application.
    """
    
    _instance: Optional['MongoDBHandler'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'MongoDBHandler':
        """Implement singleton pattern for connection management."""
        if cls._instance is None:
            cls._instance = super(MongoDBHandler, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize MongoDB handler with optimized connection settings."""
        if self._initialized:
            return
            
        self.mongo_uri = config.mongo_uri
        self.db_name = config.mongo_db_name
        self._client: Optional[MongoClient] = None
        self._async_client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self._database: Optional[Database] = None
        self._connection_start_time: Optional[datetime] = None
        
        # Connection configuration optimized for high-throughput financial data
        self.connection_config = {
            'serverSelectionTimeoutMS': 30000,  # 30 seconds
            'connectTimeoutMS': 20000,          # 20 seconds
            'socketTimeoutMS': 60000,           # 60 seconds
            'maxPoolSize': 50,                  # Maximum connections in pool
            'minPoolSize': 5,                   # Minimum connections in pool
            'maxIdleTimeMS': 300000,            # 5 minutes max idle time
            'retryWrites': True,                # Enable retryable writes
            'retryReads': True,                 # Enable retryable reads
            'w': 'majority',                    # Write concern for durability
            'readPreference': 'primary',        # Read from primary for consistency
        }
        
        self._connect()
        self._initialized = True
        
        logger.info("✅ MongoDB Handler initialized successfully")
    
    def _connect(self) -> None:
        """Establish connection to MongoDB with error handling."""
        try:
            logger.info(f"🔌 Connecting to MongoDB: {self.db_name}")
            
            # Create synchronous client
            self._client = MongoClient(
                self.mongo_uri,
                **self.connection_config
            )
            
            # Create asynchronous client for async operations
            self._async_client = motor.motor_asyncio.AsyncIOMotorClient(
                self.mongo_uri,
                **self.connection_config
            )
            
            # Get database reference
            self._database = self._client[self.db_name]
            
            # Test the connection
            self._test_connection()
            
            self._connection_start_time = datetime.now(timezone.utc)
            logger.info("✅ MongoDB connection established successfully")
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            raise MongoDBConnectionError(
                f"❌ Failed to connect to MongoDB: {str(e)}. "
                f"Please check your MONGO_URI and network connectivity."
            )
        except PyMongoConfigError as e:
            raise MongoDBConnectionError(
                f"❌ MongoDB configuration error: {str(e)}. "
                f"Please check your connection string format."
            )
        except Exception as e:
            raise MongoDBConnectionError(
                f"❌ Unexpected MongoDB connection error: {str(e)}"
            )
    
    def _test_connection(self) -> None:
        """Test the MongoDB connection by performing a simple operation."""
        try:
            # Ping the server
            self._client.admin.command('ping')
            
            # Test database access
            self._database.list_collection_names()
            
            logger.info("✅ MongoDB connection test passed")
            
        except Exception as e:
            raise MongoDBConnectionError(
                f"❌ MongoDB connection test failed: {str(e)}"
            )
    
    @property
    def client(self) -> MongoClient:
        """Get the synchronous MongoDB client."""
        if self._client is None:
            raise MongoDBConnectionError("MongoDB client not initialized")
        return self._client
    
    @property
    def async_client(self) -> motor.motor_asyncio.AsyncIOMotorClient:
        """Get the asynchronous MongoDB client."""
        if self._async_client is None:
            raise MongoDBConnectionError("Async MongoDB client not initialized")
        return self._async_client
    
    @property
    def database(self) -> Database:
        """Get the database reference."""
        if self._database is None:
            raise MongoDBConnectionError("Database not initialized")
        return self._database
    
    def get_collection(self, collection_name: str) -> Collection:
        """
        Get a collection reference.
        
        Args:
            collection_name (str): Name of the collection
            
        Returns:
            Collection: MongoDB collection reference
        """
        return self.database[collection_name]
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a comprehensive health check of the MongoDB connection.
        
        Returns:
            Dict containing health status and connection metrics
        """
        try:
            start_time = time.time()
            
            # Test basic connectivity
            self._client.admin.command('ping')
            ping_time = time.time() - start_time
            
            # Get server status
            server_status = self._client.admin.command('serverStatus')
            
            # Get database stats
            db_stats = self._database.command('dbStats')
            
            # Calculate uptime
            uptime_seconds = None
            if self._connection_start_time:
                uptime_seconds = (
                    datetime.now(timezone.utc) - self._connection_start_time
                ).total_seconds()
            
            return {
                'status': 'healthy',
                'connection': {
                    'ping_time_ms': round(ping_time * 1000, 2),
                    'uptime_seconds': uptime_seconds,
                    'server_version': server_status.get('version'),
                    'max_pool_size': self.connection_config['maxPoolSize'],
                    'min_pool_size': self.connection_config['minPoolSize']
                },
                'database': {
                    'name': self.db_name,
                    'collections': db_stats.get('collections', 0),
                    'data_size_mb': round(db_stats.get('dataSize', 0) / (1024*1024), 2),
                    'index_size_mb': round(db_stats.get('indexSize', 0) / (1024*1024), 2)
                },
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ MongoDB health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get detailed connection pool statistics.
        
        Returns:
            Dict containing connection pool metrics
        """
        try:
            pool_stats = self._client.topology_description.server_descriptions()
            
            stats = {
                'pool_stats': {},
                'topology_type': str(self._client.topology_description.topology_type),
                'servers': len(pool_stats)
            }
            
            for server_address, server_desc in pool_stats.items():
                stats['pool_stats'][str(server_address)] = {
                    'server_type': str(server_desc.server_type),
                    'round_trip_time': server_desc.round_trip_time,
                    'is_writable': server_desc.is_writable,
                    'is_readable': server_desc.is_readable
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get connection stats: {e}")
            return {'error': str(e)}
    
    def close_connections(self) -> None:
        """Gracefully close all MongoDB connections."""
        try:
            if self._client:
                self._client.close()
                logger.info("🔌 Synchronous MongoDB client closed")
            
            if self._async_client:
                self._async_client.close()
                logger.info("🔌 Asynchronous MongoDB client closed")
                
        except Exception as e:
            logger.error(f"❌ Error closing MongoDB connections: {e}")
    
    def reconnect(self) -> None:
        """Reconnect to MongoDB (useful for connection recovery)."""
        logger.info("🔄 Reconnecting to MongoDB...")
        self.close_connections()
        self._connect()
        logger.info("✅ MongoDB reconnection completed")
    
    def __del__(self):
        """Cleanup method to ensure connections are closed."""
        self.close_connections()
    
    def __repr__(self) -> str:
        """String representation of the MongoDB handler."""
        return (
            f"MongoDBHandler("
            f"db='{self.db_name}', "
            f"connected={self._client is not None}, "
            f"pool_size={self.connection_config['maxPoolSize']}"
            f")"
        )

# Global MongoDB handler instance
try:
    mongodb = MongoDBHandler()
    logger.info("🚀 Global MongoDB handler instance created successfully")
except MongoDBConnectionError as e:
    logger.error(f"💥 MongoDB initialization failed: {e}")
    raise
except Exception as e:
    logger.error(f"💥 Unexpected MongoDB error: {e}")
    raise

# Convenience exports for easy importing
__all__ = [
    'mongodb',
    'MongoDBHandler',
    'MongoDBConnectionError'
]

# Quick access to commonly used components
CLIENT = mongodb.client
DATABASE = mongodb.database
ASYNC_CLIENT = mongodb.async_client