#!/usr/bin/env python3
"""
Debug script to examine actual symbol names in the database
and fix the universe manager symbol matching
"""

print("🔍 Debugging Symbol Names in Database...")
print("=" * 60)

try:
    from database.collections import get_instruments_master
    
    collection = get_instruments_master()
    
    # 1. Find all INDEX instruments
    print("\n📊 Step 1: Finding All INDEX Instruments...")
    index_instruments = list(collection.find(
        {'INSTRUMENT': 'INDEX'},
        {'SYMBOL_NAME': 1, 'DISPLAY_NAME': 1, 'SECURITY_ID': 1}
    ).limit(20))
    
    print(f"Found {len(index_instruments)} INDEX instruments:")
    for inst in index_instruments:
        print(f"   ID {inst['SECURITY_ID']}: '{inst['SYMBOL_NAME']}' | Display: '{inst['DISPLAY_NAME']}'")
    
    # 2. Search for variations of Nifty names
    print(f"\n🔍 Step 2: Searching for Nifty Variations...")
    nifty_patterns = [
        {'SYMBOL_NAME': {'$regex': 'NIFTY', '$options': 'i'}},
        {'DISPLAY_NAME': {'$regex': 'NIFTY', '$options': 'i'}},
        {'SYMBOL_NAME': {'$regex': 'BANK', '$options': 'i'}},
        {'DISPLAY_NAME': {'$regex': 'BANK', '$options': 'i'}}
    ]
    
    for i, pattern in enumerate(nifty_patterns, 1):
        results = list(collection.find(
            {'INSTRUMENT': 'INDEX', **pattern},
            {'SYMBOL_NAME': 1, 'DISPLAY_NAME': 1, 'SECURITY_ID': 1}
        ).limit(10))
        
        print(f"\n   Pattern {i} Results:")
        for inst in results:
            print(f"      ID {inst['SECURITY_ID']}: '{inst['SYMBOL_NAME']}' | Display: '{inst['DISPLAY_NAME']}'")
    
    # 3. Find sample equity instruments
    print(f"\n📈 Step 3: Finding Sample EQUITY Instruments...")
    equity_samples = list(collection.find(
        {'INSTRUMENT': 'EQUITY', 'SERIES': 'EQ'},
        {'SYMBOL_NAME': 1, 'DISPLAY_NAME': 1, 'SECURITY_ID': 1}
    ).limit(20))
    
    print(f"Found {len(equity_samples)} EQUITY instruments (showing first 20):")
    for inst in equity_samples:
        print(f"   ID {inst['SECURITY_ID']}: '{inst['SYMBOL_NAME']}' | Display: '{inst['DISPLAY_NAME']}'")
    
    # 4. Check for specific stocks we expect
    print(f"\n🏢 Step 4: Searching for Expected Stocks...")
    expected_stocks = ['RELIANCE', 'TCS', 'HDFCBANK', 'ICICIBANK', 'SBIN']
    
    for stock in expected_stocks:
        result = collection.find_one(
            {'INSTRUMENT': 'EQUITY', 'SYMBOL_NAME': stock},
            {'SYMBOL_NAME': 1, 'DISPLAY_NAME': 1, 'SECURITY_ID': 1}
        )
        
        if result:
            print(f"   ✅ Found {stock}: ID {result['SECURITY_ID']} | Display: '{result['DISPLAY_NAME']}'")
        else:
            # Try case-insensitive search
            result = collection.find_one(
                {'INSTRUMENT': 'EQUITY', 'SYMBOL_NAME': {'$regex': f'^{stock}$', '$options': 'i'}},
                {'SYMBOL_NAME': 1, 'DISPLAY_NAME': 1, 'SECURITY_ID': 1}
            )
            if result:
                print(f"   ⚠️  Found {stock} with different case: '{result['SYMBOL_NAME']}' | Display: '{result['DISPLAY_NAME']}'")
            else:
                # Try partial match
                partial_results = list(collection.find(
                    {'INSTRUMENT': 'EQUITY', 'SYMBOL_NAME': {'$regex': stock, '$options': 'i'}},
                    {'SYMBOL_NAME': 1, 'DISPLAY_NAME': 1, 'SECURITY_ID': 1}
                ).limit(3))
                
                if partial_results:
                    print(f"   🔍 Partial matches for {stock}:")
                    for res in partial_results:
                        print(f"      '{res['SYMBOL_NAME']}' | Display: '{res['DISPLAY_NAME']}'")
                else:
                    print(f"   ❌ No matches found for {stock}")
    
    # 5. Check F&O instruments
    print(f"\n📊 Step 5: Sample F&O Instruments...")
    fo_types = ['FUTIDX', 'OPTIDX', 'FUTSTK', 'OPTSTK']
    
    for fo_type in fo_types:
        count = collection.count_documents({'INSTRUMENT': fo_type})
        print(f"   {fo_type}: {count:,} instruments")
        
        if count > 0:
            samples = list(collection.find(
                {'INSTRUMENT': fo_type},
                {'SYMBOL_NAME': 1, 'DISPLAY_NAME': 1, 'SECURITY_ID': 1, 'UNDERLYING_SYMBOL': 1}
            ).limit(3))
            
            for sample in samples:
                underlying = sample.get('UNDERLYING_SYMBOL', 'N/A')
                print(f"      ID {sample['SECURITY_ID']}: '{sample['SYMBOL_NAME']}' | Underlying: '{underlying}'")
    
    # 6. Summary and recommendations
    print(f"\n💡 FINDINGS & RECOMMENDATIONS:")
    print(f"=" * 50)
    
    # Count total instruments by type
    instrument_counts = {}
    pipeline = [
        {'$group': {'_id': '$INSTRUMENT', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}
    ]
    
    for result in collection.aggregate(pipeline):
        instrument_counts[result['_id']] = result['count']
    
    print(f"📊 Instrument Distribution:")
    for inst_type, count in instrument_counts.items():
        print(f"   {inst_type}: {count:,}")
    
    print(f"\n🔧 Next Steps:")
    print(f"   1. Update universe manager with correct index symbol names")
    print(f"   2. Update constituent stock symbols to match database")
    print(f"   3. Test universe discovery again")

except Exception as e:
    print(f"❌ Debug failed: {e}")
    import traceback
    traceback.print_exc()