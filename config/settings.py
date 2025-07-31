"""
DhanHQ Data Lake - Configuration Management Module

This module handles secure loading and validation of all configuration variables
including the dual API key strategy for DhanHQ and MongoDB connection settings.

Key Features:
- Dual API key setup (Firehose + Workhorse strategy)
- Environment variable validation with clear error messages
- Secure credential handling with python-dotenv
- Configuration validation and health checks
- Backward compatibility with all dhanhq library versions

Author: Data Lake Engineering Team
Version: 2.0
"""

import os
import sys
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import logging

# Try to import dhanhq with version detection
try:
    from dhanhq import dhanhq
    DHANHQ_AVAILABLE = True
except ImportError:
    dhanhq = None
    DHANHQ_AVAILABLE = False

# Configure logging for this module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    """Custom exception for configuration-related errors."""
    pass

class DhanDataLakeConfig:
    """
    Centralized configuration management for the DhanHQ Data Lake.
    
    This class implements the dual API key strategy:
    - Primary (Firehose): Dedicated for WebSocket real-time data
    - Secondary (Workhorse): Dedicated for REST API calls
    
    Compatible with all versions of dhanhq library (v1.x, v2.0.x, v2.1+)
    """
    
    def __init__(self, env_file: str = ".env"):
        """
        Initialize configuration by loading environment variables.
        
        Args:
            env_file (str): Path to the .env file
            
        Raises:
            ConfigurationError: If required variables are missing or invalid
        """
        self.env_file = env_file
        self._load_environment()
        self._validate_configuration()
        self._create_dhan_clients()
        
        logger.info("✅ Configuration loaded successfully with dual API key strategy")
    
    def _load_environment(self) -> None:
        """Load environment variables from .env file."""
        if not os.path.exists(self.env_file):
            raise ConfigurationError(
                f"❌ Environment file '{self.env_file}' not found. "
                f"Please copy .env.example to .env and configure your credentials."
            )
        
        # Load environment variables
        load_dotenv(self.env_file)
        logger.info(f"📄 Loaded environment variables from {self.env_file}")
    
    def _validate_configuration(self) -> None:
        """Validate that all required configuration variables are present."""
        required_vars = [
            "PRIMARY_DHAN_CLIENT_ID",
            "PRIMARY_DHAN_ACCESS_TOKEN", 
            "SECONDARY_DHAN_CLIENT_ID",
            "SECONDARY_DHAN_ACCESS_TOKEN",
            "MONGO_URI",
            "MONGO_DB_NAME"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ConfigurationError(
                f"❌ Missing required environment variables: {', '.join(missing_vars)}\n"
                f"Please check your .env file and ensure all variables are set."
            )
        
        # Validate API key format (should be non-empty strings)
        api_keys = [
            ("PRIMARY_DHAN_CLIENT_ID", os.getenv("PRIMARY_DHAN_CLIENT_ID")),
            ("PRIMARY_DHAN_ACCESS_TOKEN", os.getenv("PRIMARY_DHAN_ACCESS_TOKEN")),
            ("SECONDARY_DHAN_CLIENT_ID", os.getenv("SECONDARY_DHAN_CLIENT_ID")),
            ("SECONDARY_DHAN_ACCESS_TOKEN", os.getenv("SECONDARY_DHAN_ACCESS_TOKEN"))
        ]
        
        for var_name, var_value in api_keys:
            if not var_value or len(var_value.strip()) < 10:
                raise ConfigurationError(
                    f"❌ {var_name} appears to be invalid (too short or empty). "
                    f"Please check your DhanHQ API credentials."
                )
        
        # Validate MongoDB URI format
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri.startswith(("mongodb://", "mongodb+srv://")):
            raise ConfigurationError(
                f"❌ MONGO_URI must start with 'mongodb://' or 'mongodb+srv://'. "
                f"Current value: {mongo_uri[:20]}..."
            )
        
        logger.info("✅ All required configuration variables validated")
    
    def _create_dhan_clients(self) -> None:
        """Create the dual DhanHQ client objects for API access."""
        if not DHANHQ_AVAILABLE:
            raise ConfigurationError(
                "❌ DhanHQ library not available. Please install it with: pip install dhanhq"
            )
        
        try:
            # Create DhanHQ clients using the legacy v2.0.x method
            # This works with dhanhq==2.0.2 and similar versions
            
            # Primary API Key (The Firehose) - For WebSocket connections
            self.firehose_client = dhanhq(
                os.getenv("PRIMARY_DHAN_CLIENT_ID"),
                os.getenv("PRIMARY_DHAN_ACCESS_TOKEN")
            )
            
            # Secondary API Key (The Workhorse) - For REST API calls
            self.workhorse_client = dhanhq(
                os.getenv("SECONDARY_DHAN_CLIENT_ID"),
                os.getenv("SECONDARY_DHAN_ACCESS_TOKEN")
            )
            
            logger.info("🔑 Dual DhanHQ clients created successfully (v2.0.x method)")
            
        except Exception as e:
            raise ConfigurationError(
                f"❌ Failed to create DhanHQ clients: {str(e)}. "
                f"Please verify your DhanHQ API credentials are correct and library is installed properly."
            )
    
    @property
    def mongo_uri(self) -> str:
        """Get MongoDB connection URI."""
        return os.getenv("MONGO_URI")
    
    @property
    def mongo_db_name(self) -> str:
        """Get MongoDB database name."""
        return os.getenv("MONGO_DB_NAME")
    
    @property
    def log_level(self) -> str:
        """Get logging level (default: INFO)."""
        return os.getenv("LOG_LEVEL", "INFO")
    
    @property
    def log_format(self) -> str:
        """Get log format (default: json)."""
        return os.getenv("LOG_FORMAT", "json")
    
    @property
    def max_concurrent_requests(self) -> int:
        """Get maximum concurrent requests (default: 10)."""
        return int(os.getenv("MAX_CONCURRENT_REQUESTS", "10"))
    
    @property
    def rate_limit_per_second(self) -> int:
        """Get rate limit per second (default: 9 - safe buffer under 10)."""
        return int(os.getenv("RATE_LIMIT_PER_SECOND", "9"))
    
    def get_firehose_credentials(self) -> Dict[str, str]:
        """
        Get credentials for the Firehose API key (WebSocket use).
        
        Returns:
            Dict containing client_id and access_token for WebSocket connections
        """
        return {
            "client_id": os.getenv("PRIMARY_DHAN_CLIENT_ID"),
            "access_token": os.getenv("PRIMARY_DHAN_ACCESS_TOKEN")
        }
    
    def get_workhorse_credentials(self) -> Dict[str, str]:
        """
        Get credentials for the Workhorse API key (REST API use).
        
        Returns:
            Dict containing client_id and access_token for REST API calls
        """
        return {
            "client_id": os.getenv("SECONDARY_DHAN_CLIENT_ID"),
            "access_token": os.getenv("SECONDARY_DHAN_ACCESS_TOKEN")
        }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a configuration health check.
        
        Returns:
            Dict containing the health status and configuration summary
        """
        dhanhq_version = "unknown"
        try:
            import dhanhq
            dhanhq_version = getattr(dhanhq, '__version__', 'unknown')
        except:
            pass
            
        return {
            "status": "healthy",
            "dhanhq_version": dhanhq_version,
            "dhanhq_available": DHANHQ_AVAILABLE,
            "dual_api_keys": True,
            "mongodb_configured": bool(self.mongo_uri and self.mongo_db_name),
            "environment_file": self.env_file,
            "rate_limit_config": {
                "max_concurrent": self.max_concurrent_requests,
                "rate_per_second": self.rate_limit_per_second
            },
            "logging_config": {
                "level": self.log_level,
                "format": self.log_format
            }
        }
    
    def test_api_connection(self) -> Dict[str, Any]:
        """
        Test API connections for both clients.
        
        Returns:
            Dict containing connection test results
        """
        results = {
            "firehose_client": {"status": "unknown", "error": None},
            "workhorse_client": {"status": "unknown", "error": None}
        }
        
        # Test Firehose client
        try:
            # Try a simple API call that doesn't require market hours
            self.firehose_client.get_fund_limits()
            results["firehose_client"]["status"] = "connected"
            logger.info("✅ Firehose client connection test passed")
        except Exception as e:
            results["firehose_client"]["status"] = "failed"
            results["firehose_client"]["error"] = str(e)
            logger.warning(f"⚠️ Firehose client connection test failed: {e}")
        
        # Test Workhorse client
        try:
            # Try a simple API call that doesn't require market hours
            self.workhorse_client.get_fund_limits()
            results["workhorse_client"]["status"] = "connected"
            logger.info("✅ Workhorse client connection test passed")
        except Exception as e:
            results["workhorse_client"]["status"] = "failed"
            results["workhorse_client"]["error"] = str(e)
            logger.warning(f"⚠️ Workhorse client connection test failed: {e}")
        
        return results
    
    def __repr__(self) -> str:
        """String representation of the configuration."""
        return (
            f"DhanDataLakeConfig("
            f"db='{self.mongo_db_name}', "
            f"dual_keys=True, "
            f"rate_limit={self.rate_limit_per_second}/sec, "
            f"dhanhq_available={DHANHQ_AVAILABLE}"
            f")"
        )

# Global configuration instance
# This will be imported by other modules
try:
    config = DhanDataLakeConfig()
    logger.info("🚀 Global configuration instance created successfully")
except ConfigurationError as e:
    logger.error(f"💥 Configuration failed: {e}")
    sys.exit(1)
except Exception as e:
    logger.error(f"💥 Unexpected configuration error: {e}")
    sys.exit(1)

# Convenience exports for easy importing
__all__ = [
    'config',
    'DhanDataLakeConfig', 
    'ConfigurationError'
]

# Quick access to commonly used components
FIREHOSE_CLIENT = config.firehose_client
WORKHORSE_CLIENT = config.workhorse_client
MONGO_URI = config.mongo_uri
MONGO_DB_NAME = config.mongo_db_name

# Additional convenience exports
API_CREDENTIALS = {
    'firehose': config.get_firehose_credentials(),
    'workhorse': config.get_workhorse_credentials()
}