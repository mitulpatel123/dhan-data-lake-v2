"""
DhanHQ Data Lake - Asynchronous Historical Data Fetcher

This module implements a high-performance, rate-limited historical data fetcher
that can backfill OHLCV data for thousands of instruments concurrently while
respecting API limits and ensuring data integrity.

Key Features:
- Asynchronous concurrent fetching for maximum throughput
- Advanced rate limiting with token bucket algorithm
- Exponential backoff retry logic for resilience
- Bulk MongoDB insertion for performance
- Progress tracking and comprehensive logging
- 2025-compatible with latest DhanHQ API patterns

Author: Data Lake Engineering Team
Version: 2.0
Compatible: Python 3.8+ (2025 standards)
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timezone, date, timedelta
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import time
import json
from pymongo import InsertOne
from pymongo.errors import BulkWriteError

from config.settings import config
from database.collections import get_historical_ohlcv
from core.universe_manager import universe_manager

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class FetchTask:
    """Represents a single historical data fetch task."""
    security_id: int
    symbol: str
    exchange_segment: str
    instrument_type: str
    from_date: str
    to_date: str
    task_id: str
    
class RateLimitError(Exception):
    """Custom exception for rate limit violations."""
    pass

class HistoricalDataFetcher:
    """
    High-performance asynchronous historical data fetcher with advanced
    rate limiting and error handling capabilities.
    """
    
    # DhanHQ API endpoints
    DAILY_HISTORICAL_URL = "https://api.dhan.co/v2/charts/historical"
    INTRADAY_HISTORICAL_URL = "https://api.dhan.co/v2/charts/intraday"
    
    # Rate limiting configuration (conservative for production)
    MAX_CONCURRENT_REQUESTS = 8  # Conservative concurrency
    REQUESTS_PER_SECOND = 9       # Under the 10/sec limit
    REQUESTS_PER_DAY = 95000      # Under the 100k/day limit
    
    def __init__(self):
        """Initialize the historical data fetcher."""
        try:
            # Get DhanHQ client (workhorse for REST API calls)
            self.dhan_client = config.workhorse_client
            self.collection = get_historical_ohlcv()
            
            # Rate limiting components
            self.semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_REQUESTS)
            self.rate_limiter = TokenBucket(self.REQUESTS_PER_SECOND)
            self.daily_request_count = 0
            self.session: Optional[aiohttp.ClientSession] = None
            
            # Statistics tracking
            self.stats = {
                'total_tasks': 0,
                'completed_tasks': 0,
                'failed_tasks': 0,
                'total_candles': 0,
                'api_calls_made': 0,
                'start_time': None
            }
            
            logger.info("✅ HistoricalDataFetcher initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize HistoricalDataFetcher: {e}")
            raise
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30, connect=10),
            connector=aiohttp.TCPConnector(limit=50, limit_per_host=20)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def create_fetch_tasks(self, security_ids: List[int], 
                          days_back: int = 365) -> List[FetchTask]:
        """
        Create fetch tasks for the given security IDs.
        
        Args:
            security_ids: List of security IDs to fetch data for
            days_back: Number of days to fetch back from today
            
        Returns:
            List of FetchTask objects
        """
        tasks = []
        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=days_back)
        
        # Get instrument details from database
        instruments_collection = universe_manager.collection
        
        for security_id in security_ids:
            try:
                # Look up instrument details
                instrument = instruments_collection.find_one({'SECURITY_ID': security_id})
                
                if not instrument:
                    logger.warning(f"⚠️ Instrument {security_id} not found in database")
                    continue
                
                # Map instrument type to API format
                instrument_type = self._map_instrument_type(instrument.get('INSTRUMENT', ''))
                if not instrument_type:
                    logger.warning(f"⚠️ Unsupported instrument type for {security_id}")
                    continue
                
                # Map exchange segment
                exchange_segment = self._map_exchange_segment(
                    instrument.get('EXCH_ID', ''),
                    instrument.get('SEGMENT', '')
                )
                
                if not exchange_segment:
                    logger.warning(f"⚠️ Unsupported exchange segment for {security_id}")
                    continue
                
                task = FetchTask(
                    security_id=security_id,
                    symbol=instrument.get('SYMBOL_NAME', f'ID_{security_id}'),
                    exchange_segment=exchange_segment,
                    instrument_type=instrument_type,
                    from_date=start_date.strftime('%Y-%m-%d'),
                    to_date=end_date.strftime('%Y-%m-%d'),
                    task_id=f"{security_id}_{start_date}_{end_date}"
                )
                
                tasks.append(task)
                
            except Exception as e:
                logger.error(f"❌ Error creating task for {security_id}: {e}")
                continue
        
        logger.info(f"📋 Created {len(tasks)} fetch tasks for {len(security_ids)} instruments")
        return tasks
    
    def _map_instrument_type(self, instrument: str) -> Optional[str]:
        """Map database instrument type to API format."""
        mapping = {
            'EQUITY': 'EQUITY',
            'INDEX': 'INDEX',
            'FUTIDX': 'FUTIDX',
            'OPTIDX': 'OPTIDX',
            'FUTSTK': 'FUTSTK',
            'OPTSTK': 'OPTSTK',
            'FUTCOM': 'FUTCOM',
            'OPTFUT': 'OPTFUT',
            'FUTCUR': 'FUTCUR',
            'OPTCUR': 'OPTCUR'
        }
        return mapping.get(instrument.upper())
    
    def _map_exchange_segment(self, exchange: str, segment: str) -> Optional[str]:
        """Map database exchange/segment to API format."""
        if exchange == 'NSE':
            if segment == 'E':
                return 'NSE_EQ'
            elif segment == 'D':
                return 'NSE_FNO'
            elif segment == 'C':
                return 'NSE_CURRENCY'
        elif exchange == 'BSE':
            if segment == 'E':
                return 'BSE_EQ'
            elif segment == 'D':
                return 'BSE_FNO'
            elif segment == 'C':
                return 'BSE_CURRENCY'
        elif exchange == 'MCX':
            if segment == 'M':
                return 'MCX_COMM'
        
        return None
    
    @retry(
        retry=retry_if_exception_type((aiohttp.ClientError, RateLimitError, asyncio.TimeoutError)),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(5)
    )
    async def _fetch_single_instrument(self, task: FetchTask) -> Optional[Dict[str, Any]]:
        """
        Fetch historical data for a single instrument with rate limiting and retries.
        
        Args:
            task: FetchTask containing instrument details
            
        Returns:
            Dictionary containing OHLCV data or None if failed
        """
        async with self.semaphore:  # Limit concurrent requests
            await self.rate_limiter.acquire()  # Rate limiting
            
            if self.daily_request_count >= self.REQUESTS_PER_DAY:
                raise RateLimitError("Daily API request limit exceeded")
            
            try:
                # Prepare request payload
                payload = {
                    "securityId": str(task.security_id),
                    "exchangeSegment": task.exchange_segment,
                    "instrument": task.instrument_type,
                    "expiryCode": 0,  # Current expiry for derivatives
                    "oi": task.instrument_type in ['FUTIDX', 'OPTIDX', 'FUTSTK', 'OPTSTK'],
                    "fromDate": task.from_date,
                    "toDate": task.to_date
                }
                
                # Get API credentials
                headers = {
                    'access-token': config.get_workhorse_credentials()['access_token'],
                    'client-id': config.get_workhorse_credentials()['client_id'],
                    'Content-Type': 'application/json'
                }
                
                # Make API request
                async with self.session.post(
                    self.DAILY_HISTORICAL_URL,
                    json=payload,
                    headers=headers
                ) as response:
                    self.daily_request_count += 1
                    self.stats['api_calls_made'] += 1
                    
                    if response.status == 429:
                        logger.warning(f"⚠️ Rate limit hit for {task.symbol}")
                        raise RateLimitError("API rate limit exceeded")
                    
                    response.raise_for_status()
                    data = await response.json()
                    
                    # Validate response structure
                    if not self._validate_response(data):
                        logger.warning(f"⚠️ Invalid response for {task.symbol}")
                        return None
                    
                    logger.debug(f"✅ Fetched data for {task.symbol}: {len(data.get('timestamp', []))} candles")
                    return {
                        'task': task,
                        'data': data
                    }
                    
            except aiohttp.ClientResponseError as e:
                if e.status == 404:
                    logger.warning(f"⚠️ No data available for {task.symbol}")
                    return None
                else:
                    logger.error(f"❌ HTTP error for {task.symbol}: {e}")
                    raise
            
            except Exception as e:
                logger.error(f"❌ Unexpected error for {task.symbol}: {e}")
                raise
    
    def _validate_response(self, data: Dict[str, Any]) -> bool:
        """Validate API response structure."""
        required_fields = ['open', 'high', 'low', 'close', 'volume', 'timestamp']
        
        if not isinstance(data, dict):
            return False
        
        for field in required_fields:
            if field not in data:
                return False
            if not isinstance(data[field], list):
                return False
        
        # Check all arrays have the same length
        lengths = [len(data[field]) for field in required_fields]
        if len(set(lengths)) > 1:
            return False
        
        return True
    
    def _transform_to_documents(self, fetch_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Transform API response to MongoDB documents."""
        if not fetch_result:
            return []
        
        task = fetch_result['task']
        data = fetch_result['data']
        
        documents = []
        timestamps = data['timestamp']
        opens = data['open']
        highs = data['high']
        lows = data['low']
        closes = data['close']
        volumes = data['volume']
        open_interests = data.get('open_interest', [None] * len(timestamps))
        
        for i in range(len(timestamps)):
            # Convert timestamp to datetime
            dt = datetime.fromtimestamp(timestamps[i], tz=timezone.utc)
            
            doc = {
                'metadata': {
                    'security_id': task.security_id,
                    'symbol': task.symbol,
                    'exchange_segment': task.exchange_segment,
                    'instrument_type': task.instrument_type
                },
                'timestamp': dt,
                'open': float(opens[i]) if opens[i] is not None else None,
                'high': float(highs[i]) if highs[i] is not None else None,
                'low': float(lows[i]) if lows[i] is not None else None,
                'close': float(closes[i]) if closes[i] is not None else None,
                'volume': int(volumes[i]) if volumes[i] is not None else 0,
                'open_interest': int(open_interests[i]) if open_interests[i] is not None else None
            }
            
            documents.append(doc)
        
        return documents
    
    async def bulk_insert_documents(self, all_documents: List[Dict[str, Any]]) -> int:
        """
        Bulk insert documents to MongoDB with error handling.
        
        Args:
            all_documents: List of documents to insert
            
        Returns:
            Number of successfully inserted documents
        """
        if not all_documents:
            return 0
        
        try:
            # Prepare bulk operations
            operations = [InsertOne(doc) for doc in all_documents]
            
            # Execute bulk write
            result = self.collection.bulk_write(operations, ordered=False)
            
            inserted_count = result.inserted_count
            logger.info(f"✅ Bulk inserted {inserted_count:,} documents")
            
            return inserted_count
            
        except BulkWriteError as e:
            # Handle partial failures
            inserted_count = e.details.get('nInserted', 0)
            error_count = len(e.details.get('writeErrors', []))
            
            logger.warning(f"⚠️ Bulk insert partial success: {inserted_count:,} inserted, {error_count} errors")
            
            # Log first few errors for debugging
            for error in e.details.get('writeErrors', [])[:3]:
                logger.error(f"   Insert error: {error}")
            
            return inserted_count
        
        except Exception as e:
            logger.error(f"❌ Bulk insert failed: {e}")
            return 0
    
    async def fetch_historical_data_batch(self, security_ids: List[int], 
                                         days_back: int = 365,
                                         batch_size: int = 1000) -> Dict[str, Any]:
        """
        Fetch historical data for a batch of instruments.
        
        Args:
            security_ids: List of security IDs to fetch
            days_back: Number of days to fetch back
            batch_size: Number of documents to insert per batch
            
        Returns:
            Dictionary containing fetch statistics
        """
        self.stats['start_time'] = datetime.now(timezone.utc)
        
        try:
            # Create fetch tasks
            tasks = self.create_fetch_tasks(security_ids, days_back)
            self.stats['total_tasks'] = len(tasks)
            
            if not tasks:
                logger.warning("⚠️ No valid fetch tasks created")
                return self.stats
            
            logger.info(f"🚀 Starting historical data fetch for {len(tasks)} instruments")
            
            # Execute fetch tasks concurrently
            all_documents = []
            completed_tasks = 0
            
            # Process in chunks to manage memory
            chunk_size = min(50, len(tasks))  # Process 50 tasks at a time
            
            for i in range(0, len(tasks), chunk_size):
                chunk_tasks = tasks[i:i + chunk_size]
                
                logger.info(f"📊 Processing chunk {i//chunk_size + 1}/{(len(tasks)-1)//chunk_size + 1} ({len(chunk_tasks)} tasks)")
                
                # Execute chunk concurrently
                results = await asyncio.gather(
                    *[self._fetch_single_instrument(task) for task in chunk_tasks],
                    return_exceptions=True
                )
                
                # Process results
                chunk_documents = []
                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"❌ Task failed: {result}")
                        self.stats['failed_tasks'] += 1
                    elif result:
                        documents = self._transform_to_documents(result)
                        chunk_documents.extend(documents)
                        self.stats['completed_tasks'] += 1
                        completed_tasks += 1
                    else:
                        self.stats['failed_tasks'] += 1
                
                # Insert chunk documents if we have enough
                if len(chunk_documents) >= batch_size:
                    inserted = await self.bulk_insert_documents(chunk_documents)
                    self.stats['total_candles'] += inserted
                    chunk_documents = []
                else:
                    all_documents.extend(chunk_documents)
                
                # Progress update
                progress = (completed_tasks / len(tasks)) * 100
                logger.info(f"📈 Progress: {progress:.1f}% ({completed_tasks}/{len(tasks)})")
            
            # Insert remaining documents
            if all_documents:
                inserted = await self.bulk_insert_documents(all_documents)
                self.stats['total_candles'] += inserted
            
            # Final statistics
            duration = (datetime.now(timezone.utc) - self.stats['start_time']).total_seconds()
            self.stats['duration_seconds'] = duration
            
            logger.info(f"🎉 Historical data fetch completed!")
            logger.info(f"   Total tasks: {self.stats['total_tasks']}")
            logger.info(f"   Completed: {self.stats['completed_tasks']}")
            logger.info(f"   Failed: {self.stats['failed_tasks']}")
            logger.info(f"   Total candles: {self.stats['total_candles']:,}")
            logger.info(f"   Duration: {duration:.2f}s")
            logger.info(f"   API calls: {self.stats['api_calls_made']}")
            
            return self.stats
            
        except Exception as e:
            logger.error(f"❌ Batch fetch failed: {e}")
            import traceback
            traceback.print_exc()
            return self.stats

class TokenBucket:
    """Token bucket algorithm for rate limiting."""
    
    def __init__(self, rate_per_second: float):
        self.rate = rate_per_second
        self.tokens = rate_per_second
        self.last_update = time.time()
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire a token, waiting if necessary."""
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(self.rate, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            if self.tokens >= 1:
                self.tokens -= 1
                return
            
            # Wait for token to become available
            wait_time = (1 - self.tokens) / self.rate
            await asyncio.sleep(wait_time)
            self.tokens = 0

# Global historical fetcher instance
historical_fetcher = HistoricalDataFetcher()

# Convenience exports
__all__ = [
    'historical_fetcher',
    'HistoricalDataFetcher',
    'FetchTask',
    'RateLimitError'
]

