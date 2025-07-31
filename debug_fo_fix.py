#!/usr/bin/env python3
"""
Fixed F&O Discovery Debug Script - Handles timezone-aware dates properly
"""

print("🔍 Debugging F&O Contract Discovery (FIXED)...")
print("=" * 60)

try:
    from database.collections import get_instruments_master
    from datetime import datetime, timezone
    import pytz
    
    collection = get_instruments_master()
    
    # 1. Check F&O by UNDERLYING_SYMBOL (not UNDERLYING_SECURITY_ID)
    print("\n📊 Step 1: F&O Discovery by UNDERLYING_SYMBOL...")
    
    # These are the actual index symbols from your data
    index_symbols = ['NIFTY', 'BANKNIFTY', 'NIFTY FIN SERVICE']
    
    for symbol in index_symbols:
        print(f"\n🎯 Index: {symbol}")
        
        # Count F&O contracts
        for fo_type in ['FUTIDX', 'OPTIDX']:
            count = collection.count_documents({
                'INSTRUMENT': fo_type,
                'UNDERLYING_SYMBOL': symbol
            })
            print(f"   {fo_type}: {count:,} contracts")
            
            # Show samples
            if count > 0:
                samples = list(collection.find({
                    'INSTRUMENT': fo_type,
                    'UNDERLYING_SYMBOL': symbol
                }).limit(3))
                
                for sample in samples:
                    expiry = sample.get('SM_EXPIRY_DATE')
                    print(f"      Sample: {sample.get('SYMBOL_NAME')} | Expiry: {expiry}")
    
    # 2. Fix date comparison issue
    print("\n📅 Step 2: Testing Date Filtering (FIXED)...")
    
    # Get today's date (timezone-aware)
    today = datetime.now(timezone.utc)
    
    # Test active contract filter
    active_filter = {
        'INSTRUMENT': {'$in': ['FUTIDX', 'OPTIDX']},
        'UNDERLYING_SYMBOL': {'$in': index_symbols},
        '$or': [
            {'SM_EXPIRY_DATE': {'$gte': today}},
            {'SM_EXPIRY_DATE': None}
        ]
    }
    
    active_count = collection.count_documents(active_filter)
    print(f"\n✅ Active F&O contracts found: {active_count:,}")
    
    # 3. Show expiry distribution
    print("\n📊 Step 3: Expiry Distribution...")
    
    pipeline = [
        {'$match': {
            'INSTRUMENT': {'$in': ['FUTIDX', 'OPTIDX']},
            'UNDERLYING_SYMBOL': {'$in': index_symbols}
        }},
        {'$group': {
            '_id': '$SM_EXPIRY_DATE',
            'count': {'$sum': 1}
        }},
        {'$sort': {'_id': 1}},
        {'$limit': 10}
    ]
    
    expiry_dist = list(collection.aggregate(pipeline))
    
    for exp in expiry_dist:
        expiry_date = exp['_id']
        count = exp['count']
        if expiry_date:
            status = "Active" if expiry_date >= today else "Expired"
            print(f"   {expiry_date.strftime('%Y-%m-%d') if hasattr(expiry_date, 'strftime') else expiry_date}: {count} contracts ({status})")

except Exception as e:
    print(f"❌ Debug failed: {e}")
    import traceback
    traceback.print_exc()