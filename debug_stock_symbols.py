#!/usr/bin/env python3
"""
Enhanced script to discover the actual stock symbol format in your database
This will help us understand why the constituent stocks weren't found
"""

print("🔍 Enhanced Stock Symbol Discovery...")
print("=" * 60)

try:
    from database.collections import get_instruments_master
    
    collection = get_instruments_master()
    
    # 1. Get general statistics about equity instruments
    print("\n📊 Step 1: Equity Instruments Overview...")
    
    equity_count = collection.count_documents({'INSTRUMENT': 'EQUITY'})
    eq_series_count = collection.count_documents({'INSTRUMENT': 'EQUITY', 'SERIES': 'EQ'})
    
    print(f"   Total EQUITY instruments: {equity_count:,}")
    print(f"   EQUITY with SERIES='EQ': {eq_series_count:,}")
    
    # 2. Sample equity instruments to understand the format
    print(f"\n📝 Step 2: Sample Equity Instruments...")
    
    sample_equities = list(collection.find(
        {'INSTRUMENT': 'EQUITY', 'SERIES': 'EQ'},
        {'SYMBOL_NAME': 1, 'DISPLAY_NAME': 1, 'SECURITY_ID': 1}
    ).limit(20))
    
    print("Sample equity symbols in database:")
    for equity in sample_equities:
        symbol = equity.get('SYMBOL_NAME', 'N/A')
        display = equity.get('DISPLAY_NAME', 'N/A')
        sec_id = equity.get('SECURITY_ID', 'N/A')
        print(f"   ID {sec_id}: '{symbol}' | Display: '{display}'")
    
    # 3. Search for partial matches of expected stocks
    print(f"\n🔍 Step 3: Searching for Expected Stocks with Partial Matching...")
    
    expected_stocks = [
        'RELIANCE', 'TCS', 'HDFCBANK', 'ICICIBANK', 'SBIN',
        'INFOSYS', 'HINDUNILVR', 'ITC', 'LT', 'BAJFINANCE'
    ]
    
    found_stocks = []
    for stock in expected_stocks:
        print(f"\n   Searching for '{stock}':")
        
        # Try multiple search strategies
        searches = [
            # Exact match
            {'INSTRUMENT': 'EQUITY', 'SYMBOL_NAME': stock, 'SERIES': 'EQ'},
            # Case insensitive
            {'INSTRUMENT': 'EQUITY', 'SYMBOL_NAME': {'$regex': f'^{stock}$', '$options': 'i'}, 'SERIES': 'EQ'},
            # Partial match in symbol
            {'INSTRUMENT': 'EQUITY', 'SYMBOL_NAME': {'$regex': stock, '$options': 'i'}, 'SERIES': 'EQ'},
            # Partial match in display name
            {'INSTRUMENT': 'EQUITY', 'DISPLAY_NAME': {'$regex': stock, '$options': 'i'}, 'SERIES': 'EQ'},
        ]
        
        found_any = False
        for i, search_query in enumerate(searches, 1):
            results = list(collection.find(search_query).limit(3))
            
            if results:
                print(f"      Strategy {i}: Found {len(results)} matches")
                for res in results:
                    symbol = res.get('SYMBOL_NAME', 'N/A')
                    display = res.get('DISPLAY_NAME', 'N/A')
                    sec_id = res.get('SECURITY_ID', 'N/A')
                    print(f"         ID {sec_id}: '{symbol}' | Display: '{display}'")
                    
                    if not found_any:
                        found_stocks.append({
                            'expected': stock,
                            'actual_symbol': symbol,
                            'display_name': display,
                            'security_id': sec_id
                        })
                        found_any = True
        
        if not found_any:
            print(f"      ❌ No matches found for '{stock}'")
    
    # 4. Look for common stock symbols that might indicate the format
    print(f"\n🏢 Step 4: Looking for Well-Known Company Patterns...")
    
    well_known_patterns = [
        'HDFC', 'ICICI', 'RELIANCE', 'TATA', 'BAJAJ', 'AXIS', 'KOTAK'
    ]
    
    for pattern in well_known_patterns:
        results = list(collection.find(
            {
                'INSTRUMENT': 'EQUITY',
                'SYMBOL_NAME': {'$regex': pattern, '$options': 'i'},
                'SERIES': 'EQ'
            }
        ).limit(5))
        
        if results:
            print(f"\n   Stocks matching '{pattern}':")
            for res in results:
                symbol = res.get('SYMBOL_NAME', 'N/A')
                display = res.get('DISPLAY_NAME', 'N/A')
                sec_id = res.get('SECURITY_ID', 'N/A')
                print(f"      ID {sec_id}: '{symbol}' | Display: '{display}'")
    
    # 5. Check different SERIES values
    print(f"\n📈 Step 5: Different SERIES Values for EQUITY...")
    
    series_pipeline = [
        {'$match': {'INSTRUMENT': 'EQUITY'}},
        {'$group': {'_id': '$SERIES', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}
    ]
    
    series_results = list(collection.aggregate(series_pipeline))
    
    print("EQUITY instruments by SERIES:")
    for result in series_results:
        series = result['_id'] if result['_id'] else 'null'
        count = result['count']
        print(f"   SERIES '{series}': {count:,} instruments")
    
        # Show samples for each series
        if count > 0:
            samples = list(collection.find(
                {'INSTRUMENT': 'EQUITY', 'SERIES': result['_id']},
                {'SYMBOL_NAME': 1, 'DISPLAY_NAME': 1, 'SECURITY_ID': 1}
            ).limit(3))
            
            for sample in samples:
                symbol = sample.get('SYMBOL_NAME', 'N/A')
                display = sample.get('DISPLAY_NAME', 'N/A')
                sec_id = sample.get('SECURITY_ID', 'N/A')
                print(f"      Example: ID {sec_id}: '{symbol}' | '{display}'")
    
    # 6. Summary and recommendations
    print(f"\n💡 SUMMARY & RECOMMENDATIONS:")
    print(f"=" * 60)
    
    print(f"✅ Total equity instruments available: {equity_count:,}")
    print(f"✅ EQ series instruments: {eq_series_count:,}")
    print(f"✅ Found matches for expected stocks: {len(found_stocks)}/10")
    
    if found_stocks:
        print(f"\n🎯 Successfully Matched Stocks:")
        for stock in found_stocks:
            print(f"   {stock['expected']} → '{stock['actual_symbol']}' (ID: {stock['security_id']})")
    
    print(f"\n📝 Recommendations:")
    if len(found_stocks) > 5:
        print(f"   ✅ Good stock coverage found! Update universe manager with actual symbols.")
    elif len(found_stocks) > 0:
        print(f"   ⚠️ Partial coverage. Some stocks found, check symbol variations.")
    else:
        print(f"   ❌ No major stocks found. Check if data contains NSE equity symbols.")
        
    print(f"   💡 Consider using the most common SERIES value for equity filtering.")
    print(f"   💡 Look at the display names - they might be more standardized.")

except Exception as e:
    print(f"❌ Enhanced stock discovery failed: {e}")
    import traceback
    traceback.print_exc()