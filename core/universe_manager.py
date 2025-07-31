"""
DhanHQ Data Lake - Trading Universe Discovery Engine (FIXED VERSION)

This module intelligently discovers and manages the complete trading universe
for F&O contracts related to major Indian indices and their constituents.

FIXED: Updated with correct symbol names from database debug results.

Key Features:
- Dynamic discovery of Nifty 50, Bank Nifty, Fin Nifty contracts
- Automatic identification of constituent stocks and their F&O contracts
- Smart filtering of active contracts (non-expired)
- Comprehensive error handling and validation
- Future-proof design with 2025+ compatibility
- Extensible architecture for adding new indices

Universe Coverage:
- Index Spots: Nifty 50, Bank Nifty, Fin Nifty
- Index F&O: All futures and options for above indices
- Stock Universe: All constituent stocks from above indices
- Stock F&O: All futures and options for constituent stocks
- Total Coverage: ~5,000-10,000 active F&O contracts

Author: Data Lake Engineering Team
Version: 2.1 - FIXED SYMBOL NAMES
Compatible: Python 3.8+ (2025 standards)
"""

import logging
from typing import Dict, List, Set, Any, Optional, Tuple
from datetime import datetime, timezone, date, timedelta
from dataclasses import dataclass
from enum import Enum
from database.collections import get_instruments_master
from config.settings import config

# Configure logging
logger = logging.getLogger(__name__)

class IndexType(Enum):
    """Enumeration for supported index types - CORRECTED SYMBOL NAMES."""
    NIFTY_50 = "NIFTY"                    # ID: 13, Display: "Nifty 50"
    BANK_NIFTY = "BANKNIFTY"             # ID: 25, Display: "Nifty Bank"  
    FIN_NIFTY = "NIFTY FIN SERVICE"      # ID: 27, Display: "FinNifty"

class InstrumentClass(Enum):
    """Enumeration for instrument classes."""
    INDEX = "INDEX"
    EQUITY = "EQUITY"
    INDEX_FUTURE = "FUTIDX"
    INDEX_OPTION = "OPTIDX"
    STOCK_FUTURE = "FUTSTK"
    STOCK_OPTION = "OPTSTK"

@dataclass
class UniverseStats:
    """Statistics about the discovered universe."""
    total_instruments: int
    index_spots: int
    index_futures: int
    index_options: int
    stocks: int
    stock_futures: int
    stock_options: int
    discovery_timestamp: datetime
    active_expiries: List[str]

class UniverseDiscoveryError(Exception):
    """Custom exception for universe discovery errors."""
    pass

class TradingUniverseManager:
    """
    Manages the discovery and maintenance of the complete trading universe
    for algorithmic trading operations focused on major Indian indices.
    
    This class provides intelligent filtering of the complete instrument
    master to identify only the F&O contracts relevant for trading.
    """
    
    # Updated constituent lists based on actual database symbols
    # These are the actual symbol names found in the database
    NIFTY_50_CONSTITUENTS = {
        'RELIANCE INDUSTRIES LTD', 'TATA CONSULTANCY SERV LT', 'HDFC BANK LIMITED', 
        'BHARTI AIRTEL LIMITED', 'ICICI BANK LTD.', 'STATE BANK OF INDIA', 'INFOSYS LIMITED', 
        'HINDUSTAN UNILEVER LTD.', 'ITC LTD', 'LARSEN & TOUBRO LTD.', 'SUN PHARMA INDS LTD', 
        'HCL TECHNOLOGIES LTD', 'BAJAJ FINANCE LIMITED', 'MARUTI SUZUKI INDIA LTD.', 
        'KOTAK MAHINDRA BANK LTD', 'ULTRATECH CEMENT LIMITED', 'AXIS BANK LIMITED', 
        'NTPC LTD', 'ASIAN PAINTS LIMITED', 'NESTLE INDIA LIMITED',
        'BAJAJ FINSERV LTD.', 'OIL AND NATURAL GAS CORP.', 'MAHINDRA & MAHINDRA LTD', 
        'TATA STEEL LIMITED', 'TITAN COMPANY LIMITED', 'POWER GRID CORP. OF INDIA', 'COAL INDIA LTD',
        'ADANI PORTS & SEZ LTD', 'WIPRO LIMITED', 'TATA MOTORS LIMITED', 'APOLLO HOSPITALS ENTER LTD', 
        'DIVI\'S LABORATORIES LTD', 'EICHER MOTORS LTD', 'JSW STEEL LIMITED', 'BHARAT PETROLEUM CORP LTD', 
        'TATA CONSUMER PROD LTD', 'TECH MAHINDRA LIMITED', 'GRASIM INDUSTRIES LTD', 'HINDALCO INDUSTRIES LTD', 
        'SBI LIFE INSURANCE CO LTD', 'HERO MOTOCORP LIMITED', 'INDUSIND BANK LIMITED', 'CIPLA LIMITED', 
        'HDFC LIFE INS CO LTD', 'BAJAJ AUTO LIMITED', 'ADANI ENTERPRISES LTD', 'LTI MINDTREE LIMITED', 
        'DR. REDDY\'S LABORATORIES', 'BRITANNIA INDUSTRIES LTD', 'TRENT LTD'
    }
    
    BANK_NIFTY_CONSTITUENTS = {
        'HDFC BANK LIMITED', 'ICICI BANK LTD.', 'STATE BANK OF INDIA', 'KOTAK MAHINDRA BANK LTD', 
        'AXIS BANK LIMITED', 'INDUSIND BANK LIMITED', 'AU SMALL FINANCE BANK LTD', 'BANK OF BARODA', 
        'PUNJAB NATIONAL BANK', 'IDFC FIRST BANK LIMITED', 'FEDERAL BANK LTD', 'BANDHAN BANK LIMITED'
    }
    
    FIN_NIFTY_CONSTITUENTS = {
        'BAJAJ FINANCE LIMITED', 'BAJAJ FINSERV LTD.', 'HDFC BANK LIMITED', 'ICICI BANK LTD.', 
        'STATE BANK OF INDIA', 'KOTAK MAHINDRA BANK LTD', 'AXIS BANK LIMITED', 'HDFC LIFE INS CO LTD', 
        'SBI LIFE INSURANCE CO LTD', 'ICICI LOMBARD GIC LTD', 'ICICI PRU LIFE INS CO LTD', 
        'BAJAJ HOLDINGS & INVS LTD', 'POWER FINANCE CORP LTD', 'REC LIMITED', 'INDUSIND BANK LIMITED', 
        'MAHINDRA & MAHINDRA FIN', 'CHOLAMANDALAM INV FIN CO', 'MUTHOOT FINANCE LIMITED', 
        'HDFC ASSET MGMT CO LTD', 'SBI CARDS & PAYMENT SER'
    }
    
    def __init__(self):
        """Initialize the trading universe manager."""
        try:
            self.collection = get_instruments_master()
            self._validate_collection()
            
            # Cache for discovered instruments
            self._universe_cache: Optional[Dict[str, List[Dict]]] = None
            self._cache_timestamp: Optional[datetime] = None
            self._cache_expiry_hours = 6  # Cache expires after 6 hours
            
            # Discovered stock symbols (will be populated dynamically)
            self._discovered_stock_symbols: Optional[Set[str]] = None
            
            logger.info("✅ TradingUniverseManager initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize TradingUniverseManager: {e}")
            raise UniverseDiscoveryError(f"Initialization failed: {str(e)}")
    
    def _validate_collection(self) -> None:
        """Validate that the instruments collection is properly set up."""
        try:
            count = self.collection.count_documents({})
            if count == 0:
                raise UniverseDiscoveryError(
                    "Instruments collection is empty. Run instrument master sync first."
                )
            logger.info(f"📊 Instruments collection validated: {count:,} documents")
            
        except Exception as e:
            raise UniverseDiscoveryError(f"Collection validation failed: {str(e)}")
    
    def _discover_actual_stock_symbols(self) -> Set[str]:
        """
        Discover actual stock symbols in the database that match our expected constituents.
        This handles cases where symbol format might be different than expected.
        """
        if self._discovered_stock_symbols is not None:
            return self._discovered_stock_symbols
        
        logger.info("🔍 Discovering actual stock symbols in database...")
        
        # Combine all expected constituents
        all_expected = (
            self.NIFTY_50_CONSTITUENTS | 
            self.BANK_NIFTY_CONSTITUENTS | 
            self.FIN_NIFTY_CONSTITUENTS
        )
        
        discovered_symbols = set()
        
        # Try multiple search strategies
        for expected_symbol in all_expected:
            try:
                # Strategy 1: Exact match
                result = self.collection.find_one({
                    'INSTRUMENT': 'EQUITY',
                    'SYMBOL_NAME': expected_symbol,
                    'SERIES': 'EQ'
                })
                
                if result:
                    discovered_symbols.add(result['SYMBOL_NAME'])
                    continue
                
                # Strategy 2: Case-insensitive match
                result = self.collection.find_one({
                    'INSTRUMENT': 'EQUITY',
                    'SYMBOL_NAME': {'$regex': f'^{expected_symbol}$', '$options': 'i'},
                    'SERIES': 'EQ'
                })
                
                if result:
                    discovered_symbols.add(result['SYMBOL_NAME'])
                    continue
                
                # Strategy 3: Partial match in display name
                result = self.collection.find_one({
                    'INSTRUMENT': 'EQUITY',
                    'DISPLAY_NAME': {'$regex': expected_symbol, '$options': 'i'},
                    'SERIES': 'EQ'
                })
                
                if result:
                    discovered_symbols.add(result['SYMBOL_NAME'])
                    continue
                
                # Strategy 4: Search for common variations
                variations = [
                    expected_symbol.replace('-', ''),  # Remove hyphens
                    expected_symbol.replace('&', ''),   # Remove ampersands
                    expected_symbol.replace(' ', ''),   # Remove spaces
                ]
                
                for variation in variations:
                    result = self.collection.find_one({
                        'INSTRUMENT': 'EQUITY',
                        'SYMBOL_NAME': {'$regex': f'^{variation}$', '$options': 'i'},
                        'SERIES': 'EQ'
                    })
                    
                    if result:
                        discovered_symbols.add(result['SYMBOL_NAME'])
                        break
                
            except Exception as e:
                logger.warning(f"⚠️ Error searching for {expected_symbol}: {e}")
                continue
        
        self._discovered_stock_symbols = discovered_symbols
        
        coverage_pct = (len(discovered_symbols) / len(all_expected)) * 100
        logger.info(f"📈 Stock symbol discovery: {len(discovered_symbols)}/{len(all_expected)} ({coverage_pct:.1f}%)")
        
        if len(discovered_symbols) < len(all_expected) * 0.5:  # Less than 50% found
            logger.warning(f"⚠️ Low stock coverage. Expected symbols might use different format.")
            
            # Log some examples of what we actually have
            sample_stocks = list(self.collection.find(
                {'INSTRUMENT': 'EQUITY', 'SERIES': 'EQ'},
                {'SYMBOL_NAME': 1, 'DISPLAY_NAME': 1}
            ).limit(10))
            
            logger.info("📝 Sample stock symbols in database:")
            for stock in sample_stocks:
                logger.info(f"   '{stock['SYMBOL_NAME']}' | '{stock.get('DISPLAY_NAME', 'N/A')}'")
        
        return discovered_symbols
    
    def discover_complete_universe(self, force_refresh: bool = False) -> Dict[str, List[Dict]]:
        """
        Discover the complete trading universe with intelligent caching.
        
        Args:
            force_refresh (bool): Force refresh even if cache is valid
            
        Returns:
            Dict containing organized instrument lists by category
            
        Raises:
            UniverseDiscoveryError: If discovery fails
        """
        # Check cache validity
        if not force_refresh and self._is_cache_valid():
            logger.info("📊 Using cached universe data")
            return self._universe_cache.copy()
        
        logger.info("🔍 Discovering complete trading universe...")
        start_time = datetime.now(timezone.utc)
        
        try:
            universe = {
                'index_spots': [],
                'index_futures': [],
                'index_options': [],
                'stocks': [],
                'stock_futures': [],
                'stock_options': []
            }
            
            # Step 1: Discover index spots (using corrected symbol names)
            universe['index_spots'] = self._discover_index_spots()
            logger.info(f"✅ Found {len(universe['index_spots'])} index spots")
            
            # Step 2: Discover index F&O
            universe['index_futures'] = self._discover_index_futures()
            universe['index_options'] = self._discover_index_options()
            logger.info(f"✅ Found {len(universe['index_futures'])} index futures")
            logger.info(f"✅ Found {len(universe['index_options'])} index options")
            
            # Step 3: Discover constituent stocks (with smart symbol discovery)
            universe['stocks'] = self._discover_constituent_stocks()
            logger.info(f"✅ Found {len(universe['stocks'])} constituent stocks")
            
            # Step 4: Discover stock F&O
            stock_symbols = {stock['SYMBOL_NAME'] for stock in universe['stocks']}
            universe['stock_futures'] = self._discover_stock_futures(stock_symbols)
            universe['stock_options'] = self._discover_stock_options(stock_symbols)
            logger.info(f"✅ Found {len(universe['stock_futures'])} stock futures")
            logger.info(f"✅ Found {len(universe['stock_options'])} stock options")
            
            # Update cache
            self._universe_cache = universe
            self._cache_timestamp = datetime.now(timezone.utc)
            
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.info(f"🎉 Universe discovery completed in {duration:.2f}s")
            
            return universe.copy()
            
        except Exception as e:
            logger.error(f"❌ Universe discovery failed: {e}")
            raise UniverseDiscoveryError(f"Discovery failed: {str(e)}")
    
    def _is_cache_valid(self) -> bool:
        """Check if cached universe data is still valid."""
        if not self._universe_cache or not self._cache_timestamp:
            return False
        
        expiry = self._cache_timestamp + timedelta(hours=self._cache_expiry_hours)
        return datetime.now(timezone.utc) < expiry
    
    def _discover_index_spots(self) -> List[Dict]:
        """Discover spot price instruments for major indices."""
        try:
            # Use the corrected symbol names
            expected_symbols = [idx.value for idx in IndexType]
            
            query = {
                'INSTRUMENT': 'INDEX',
                'SYMBOL_NAME': {'$in': expected_symbols}
            }
            
            instruments = list(self.collection.find(query))
            
            # Validate we found all expected indices
            found_symbols = {inst['SYMBOL_NAME'] for inst in instruments}
            expected_symbols_set = set(expected_symbols)
            missing = expected_symbols_set - found_symbols
            
            if missing:
                logger.warning(f"⚠️ Missing index spots: {missing}")
            
            # Log what we found
            for inst in instruments:
                logger.info(f"   ✅ Found index: {inst['SYMBOL_NAME']} (ID: {inst['SECURITY_ID']}) - {inst.get('DISPLAY_NAME', 'N/A')}")
            
            return instruments
            
        except Exception as e:
            logger.error(f"❌ Failed to discover index spots: {e}")
            return []
    
    def _discover_index_futures(self) -> List[Dict]:
        """Discover active index futures contracts."""
        try:
            # Get underlying security IDs for our indices
            index_spots = self._discover_index_spots()
            if not index_spots:
                logger.warning("⚠️ No index spots found for futures discovery")
                return []
            
            underlying_ids = [inst['SECURITY_ID'] for inst in index_spots]
            
            query = {
                'INSTRUMENT': 'FUTIDX',
                'UNDERLYING_SECURITY_ID': {'$in': underlying_ids},
                **self._get_active_contract_filter()
            }
            
            instruments = list(self.collection.find(query))
            logger.info(f"📈 Discovered {len(instruments)} active index futures")
            
            return instruments
            
        except Exception as e:
            logger.error(f"❌ Failed to discover index futures: {e}")
            return []
    
    def _discover_index_options(self) -> List[Dict]:
        """Discover active index options contracts."""
        try:
            # Get underlying security IDs for our indices
            index_spots = self._discover_index_spots()
            if not index_spots:
                logger.warning("⚠️ No index spots found for options discovery")
                return []
            
            underlying_ids = [inst['SECURITY_ID'] for inst in index_spots]
            
            query = {
                'INSTRUMENT': 'OPTIDX',
                'UNDERLYING_SECURITY_ID': {'$in': underlying_ids},
                **self._get_active_contract_filter()
            }
            
            instruments = list(self.collection.find(query))
            logger.info(f"📊 Discovered {len(instruments)} active index options")
            
            return instruments
            
        except Exception as e:
            logger.error(f"❌ Failed to discover index options: {e}")
            return []
    
    def _discover_constituent_stocks(self) -> List[Dict]:
        """Discover all constituent stocks from major indices."""
        try:
            # Use smart symbol discovery
            discovered_symbols = self._discover_actual_stock_symbols()
            
            if not discovered_symbols:
                logger.warning("⚠️ No constituent stocks found with smart discovery")
                return []
            
            query = {
                'INSTRUMENT': 'EQUITY',
                'SYMBOL_NAME': {'$in': list(discovered_symbols)},
                'SERIES': 'EQ'
            }
            
            instruments = list(self.collection.find(query))
            
            # Log coverage information
            found_symbols = {inst['SYMBOL_NAME'] for inst in instruments}
            missing = discovered_symbols - found_symbols
            
            if missing:
                logger.warning(f"⚠️ Some discovered symbols not found in final query: {missing}")
            
            coverage = len(found_symbols) / len(discovered_symbols) * 100 if discovered_symbols else 0
            logger.info(f"📊 Stock coverage: {coverage:.1f}% ({len(found_symbols)}/{len(discovered_symbols)})")
            
            return instruments
            
        except Exception as e:
            logger.error(f"❌ Failed to discover constituent stocks: {e}")
            return []
    
    def _discover_stock_futures(self, stock_symbols: Set[str]) -> List[Dict]:
        """Discover active stock futures for given symbols."""
        try:
            if not stock_symbols:
                logger.warning("⚠️ No stock symbols provided for futures discovery")
                return []
            
            query = {
                'INSTRUMENT': 'FUTSTK',
                'UNDERLYING_SYMBOL': {'$in': list(stock_symbols)},
                **self._get_active_contract_filter()
            }
            
            instruments = list(self.collection.find(query))
            
            # Log coverage
            found_underlyings = {inst.get('UNDERLYING_SYMBOL') for inst in instruments}
            coverage = len(found_underlyings) / len(stock_symbols) * 100
            logger.info(f"📈 Stock futures coverage: {coverage:.1f}% ({len(found_underlyings)}/{len(stock_symbols)})")
            
            return instruments
            
        except Exception as e:
            logger.error(f"❌ Failed to discover stock futures: {e}")
            return []
    
    def _discover_stock_options(self, stock_symbols: Set[str]) -> List[Dict]:
        """Discover active stock options for given symbols."""
        try:
            if not stock_symbols:
                logger.warning("⚠️ No stock symbols provided for options discovery")
                return []
            
            query = {
                'INSTRUMENT': 'OPTSTK',
                'UNDERLYING_SYMBOL': {'$in': list(stock_symbols)},
                **self._get_active_contract_filter()
            }
            
            instruments = list(self.collection.find(query))
            
            # Log coverage
            found_underlyings = {inst.get('UNDERLYING_SYMBOL') for inst in instruments}
            coverage = len(found_underlyings) / len(stock_symbols) * 100
            logger.info(f"📊 Stock options coverage: {coverage:.1f}% ({len(found_underlyings)}/{len(stock_symbols)})")
            
            return instruments
            
        except Exception as e:
            logger.error(f"❌ Failed to discover stock options: {e}")
            return []
    
    def _get_active_contract_filter(self) -> Dict[str, Any]:
        """Get filter for active (non-expired) contracts."""
        today = datetime.now(timezone.utc)
        
        return {
            '$or': [
                {'SM_EXPIRY_DATE': {'$gte': today}},  # Future expiry
                {'SM_EXPIRY_DATE': None}  # No expiry (perpetual)
            ]
        }
    
    def get_security_ids_by_category(self, universe: Optional[Dict] = None) -> Dict[str, List[int]]:
        """
        Extract security IDs organized by category for easy API usage.
        
        Args:
            universe: Pre-discovered universe (optional)
            
        Returns:
            Dict with security IDs organized by instrument category
        """
        try:
            if universe is None:
                universe = self.discover_complete_universe()
            
            security_ids = {}
            
            for category, instruments in universe.items():
                security_ids[category] = [
                    inst['SECURITY_ID'] for inst in instruments 
                    if 'SECURITY_ID' in inst
                ]
            
            # Add combined lists for convenience
            security_ids['all_indices'] = (
                security_ids['index_spots'] + 
                security_ids['index_futures'] + 
                security_ids['index_options']
            )
            
            security_ids['all_stocks'] = (
                security_ids['stocks'] + 
                security_ids['stock_futures'] + 
                security_ids['stock_options']
            )
            
            security_ids['all_fo'] = (
                security_ids['index_futures'] + 
                security_ids['index_options'] + 
                security_ids['stock_futures'] + 
                security_ids['stock_options']
            )
            
            security_ids['everything'] = (
                security_ids['all_indices'] + 
                security_ids['all_stocks']
            )
            
            return security_ids
            
        except Exception as e:
            logger.error(f"❌ Failed to extract security IDs: {e}")
            raise UniverseDiscoveryError(f"Security ID extraction failed: {str(e)}")
    
    def get_universe_statistics(self, universe: Optional[Dict] = None) -> UniverseStats:
        """
        Generate comprehensive statistics about the discovered universe.
        
        Args:
            universe: Pre-discovered universe (optional)
            
        Returns:
            UniverseStats object with detailed statistics
        """
        try:
            if universe is None:
                universe = self.discover_complete_universe()
            
            # Count instruments by category
            stats = UniverseStats(
                total_instruments=sum(len(instruments) for instruments in universe.values()),
                index_spots=len(universe.get('index_spots', [])),
                index_futures=len(universe.get('index_futures', [])),
                index_options=len(universe.get('index_options', [])),
                stocks=len(universe.get('stocks', [])),
                stock_futures=len(universe.get('stock_futures', [])),
                stock_options=len(universe.get('stock_options', [])),
                discovery_timestamp=datetime.now(timezone.utc),
                active_expiries=[]
            )
            
            # Find unique expiry dates
            all_fo_instruments = (
                universe.get('index_futures', []) + 
                universe.get('index_options', []) + 
                universe.get('stock_futures', []) + 
                universe.get('stock_options', [])
            )
            
            expiry_dates = set()
            for inst in all_fo_instruments:
                expiry = inst.get('SM_EXPIRY_DATE')
                if expiry:
                    if isinstance(expiry, datetime):
                        expiry_dates.add(expiry.strftime('%Y-%m-%d'))
                    else:
                        expiry_dates.add(str(expiry))
            
            stats.active_expiries = sorted(list(expiry_dates))
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to generate universe statistics: {e}")
            raise UniverseDiscoveryError(f"Statistics generation failed: {str(e)}")
    
    def validate_universe_health(self, universe: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Perform comprehensive health checks on the discovered universe.
        
        Args:
            universe: Pre-discovered universe (optional)
            
        Returns:
            Dict containing health check results
        """
        try:
            if universe is None:
                universe = self.discover_complete_universe()
            
            health_check = {
                'status': 'healthy',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'issues': [],
                'warnings': [],
                'recommendations': []
            }
            
            stats = self.get_universe_statistics(universe)
            
            # Check minimum instrument counts
            if stats.index_spots < 3:
                health_check['issues'].append(f"Only {stats.index_spots} index spots found (expected 3)")
                health_check['status'] = 'unhealthy'
            
            if stats.stocks < 30:  # Should have significant number of stocks
                health_check['warnings'].append(f"Only {stats.stocks} stocks found (might be low)")
            
            if stats.total_instruments < 100:
                health_check['issues'].append(f"Only {stats.total_instruments} total instruments (seems low)")
                health_check['status'] = 'unhealthy'
            
            # Check F&O coverage
            fo_ratio = (stats.index_futures + stats.index_options + stats.stock_futures + stats.stock_options) / max(stats.total_instruments, 1)
            if fo_ratio < 0.1:
                health_check['warnings'].append(f"F&O coverage is {fo_ratio:.1%} (might be low)")
            
            # Check expiry dates
            if len(stats.active_expiries) < 3:
                health_check['warnings'].append(f"Only {len(stats.active_expiries)} active expiries found")
            
            # Add recommendations
            if health_check['status'] == 'healthy':
                health_check['recommendations'].append("Universe looks healthy - ready for data ingestion")
            else:
                health_check['recommendations'].append("Check instrument master sync and symbol mappings")
            
            return health_check
            
        except Exception as e:
            logger.error(f"❌ Universe health validation failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

# Global universe manager instance
try:
    universe_manager = TradingUniverseManager()
    logger.info("🚀 Global TradingUniverseManager instance created")
except Exception as e:
    logger.error(f"💥 Failed to create TradingUniverseManager: {e}")
    raise

# Convenience exports
__all__ = [
    'universe_manager',
    'TradingUniverseManager',
    'UniverseDiscoveryError',
    'UniverseStats',
    'IndexType',
    'InstrumentClass'
]