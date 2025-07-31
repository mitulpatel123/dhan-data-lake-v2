#!/usr/bin/env python3
"""
Debug script to find the correct index symbol names in your database
and fix the universe manager accordingly
"""

print("🔍 Debugging Universe Manager Symbol Names...")
print("=" * 60)

try:
    from database.collections import get_instruments_master
    
    collection = get_instruments_master()
    
    # 1. Find all INDEX instruments with comprehensive search
    print("\n📊 Step 1: Finding All INDEX Instruments...")
    
    # Search for all possible INDEX instruments
    index_instruments = list(collection.find(
        {'INSTRUMENT': 'INDEX'},
        {'SYMBOL_NAME': 1, 'DISPLAY_NAME': 1, 'SECURITY_ID': 1}
    ).sort('SECURITY_ID', 1))
    
    print(f"Found {len(index_instruments)} INDEX instruments:")
    for inst in index_instruments:
        symbol = inst.get('SYMBOL_NAME', 'N/A')
        display = inst.get('DISPLAY_NAME', 'N/A')
        sec_id = inst.get('SECURITY_ID', 'N/A')
        print(f"   ID {sec_id}: '{symbol}' | Display: '{display}'")
    
    # 2. Search specifically for Nifty-related indices
    print(f"\n🔍 Step 2: Searching for Nifty-Related Indices...")
    
    nifty_search_patterns = [
        {'SYMBOL_NAME': {'$regex': 'NIFTY.*50', '$options': 'i'}},
        {'SYMBOL_NAME': {'$regex': 'NIFTY.*BANK', '$options': 'i'}},
        {'SYMBOL_NAME': {'$regex': 'NIFTY.*FIN', '$options': 'i'}},
        {'DISPLAY_NAME': {'$regex': 'NIFTY.*50', '$options': 'i'}},
        {'DISPLAY_NAME': {'$regex': 'NIFTY.*BANK', '$options': 'i'}},
        {'DISPLAY_NAME': {'$regex': 'NIFTY.*FIN', '$options': 'i'}},
    ]
    
    found_nifty_indices = set()
    
    for i, pattern in enumerate(nifty_search_patterns, 1):
        results = list(collection.find(
            {'INSTRUMENT': 'INDEX', **pattern},
            {'SYMBOL_NAME': 1, 'DISPLAY_NAME': 1, 'SECURITY_ID': 1}
        ))
        
        if results:
            print(f"\n   Pattern {i} Results:")
            for inst in results:
                symbol = inst.get('SYMBOL_NAME', 'N/A')
                display = inst.get('DISPLAY_NAME', 'N/A')
                sec_id = inst.get('SECURITY_ID', 'N/A')
                print(f"      ID {sec_id}: '{symbol}' | Display: '{display}'")
                found_nifty_indices.add((symbol, display, sec_id))
    
    # 3. Look for specific security IDs that are commonly used
    print(f"\n🎯 Step 3: Checking Common Index Security IDs...")
    
    common_index_ids = [13, 25, 26]  # Common IDs for major indices
    for sec_id in common_index_ids:
        result = collection.find_one(
            {'SECURITY_ID': sec_id},
            {'SYMBOL_NAME': 1, 'DISPLAY_NAME': 1, 'INSTRUMENT': 1}
        )
        
        if result:
            symbol = result.get('SYMBOL_NAME', 'N/A')
            display = result.get('DISPLAY_NAME', 'N/A')
            instrument = result.get('INSTRUMENT', 'N/A')
            print(f"   ID {sec_id}: '{symbol}' | Display: '{display}' | Type: {instrument}")
    
    # 4. Generate recommended symbol mapping
    print(f"\n💡 Step 4: Recommended Symbol Mapping for Universe Manager...")
    print("Based on the findings above, update the universe manager with these symbols:")
    print("=" * 60)
    
    # Extract likely candidates
    nifty_50_candidates = []
    bank_nifty_candidates = []
    fin_nifty_candidates = []
    
    for symbol, display, sec_id in found_nifty_indices:
        symbol_upper = symbol.upper()
        display_upper = display.upper()
        
        if '50' in symbol_upper or '50' in display_upper:
            if 'BANK' not in symbol_upper and 'BANK' not in display_upper:
                nifty_50_candidates.append((symbol, display, sec_id))
        
        if 'BANK' in symbol_upper or 'BANK' in display_upper:
            bank_nifty_candidates.append((symbol, display, sec_id))
        
        if 'FIN' in symbol_upper or 'FIN' in display_upper:
            fin_nifty_candidates.append((symbol, display, sec_id))
    
    print("# Update these in core/universe_manager.py:")
    print("class IndexType(Enum):")
    
    if nifty_50_candidates:
        best_nifty = nifty_50_candidates[0]  # Take the first/best match
        print(f'    NIFTY_50 = "{best_nifty[0]}"  # ID: {best_nifty[2]}, Display: {best_nifty[1]}')
    
    if bank_nifty_candidates:
        best_bank = bank_nifty_candidates[0]
        print(f'    BANK_NIFTY = "{best_bank[0]}"  # ID: {best_bank[2]}, Display: {best_bank[1]}')
    
    if fin_nifty_candidates:
        best_fin = fin_nifty_candidates[0]
        print(f'    FIN_NIFTY = "{best_fin[0]}"  # ID: {best_fin[2]}, Display: {best_fin[1]}')
    
    # 5. Check some sample stocks
    print(f"\n📈 Step 5: Checking Sample Stock Symbols...")
    
    sample_stocks = ['RELIANCE', 'TCS', 'HDFCBANK', 'ICICIBANK', 'SBIN']
    found_stocks = []
    
    for stock in sample_stocks:
        result = collection.find_one(
            {
                'INSTRUMENT': 'EQUITY', 
                'SYMBOL_NAME': {'$regex': f'^{stock}$', '$options': 'i'},
                'SERIES': 'EQ'
            },
            {'SYMBOL_NAME': 1, 'DISPLAY_NAME': 1, 'SECURITY_ID': 1}
        )
        
        if result:
            found_stocks.append(result)
            symbol = result.get('SYMBOL_NAME', 'N/A')
            display = result.get('DISPLAY_NAME', 'N/A')
            sec_id = result.get('SECURITY_ID', 'N/A')
            print(f"   ✅ {stock}: '{symbol}' | Display: '{display}' | ID: {sec_id}")
        else:
            print(f"   ❌ {stock}: Not found")
    
    print(f"\n🎯 SUMMARY:")
    print(f"=" * 60)
    print(f"✅ Total INDEX instruments: {len(index_instruments)}")
    print(f"✅ Major indices found: {len(found_nifty_indices)}")
    print(f"✅ Sample stocks found: {len(found_stocks)}/{len(sample_stocks)}")
    
    if found_nifty_indices:
        print(f"\n🎉 SUCCESS! Found the major indices in your database.")
        print(f"📝 Next step: Update the universe manager with the correct symbol names above.")
    else:
        print(f"\n⚠️ WARNING: Could not find major indices. Check if instrument master sync worked correctly.")

except Exception as e:
    print(f"❌ Debug failed: {e}")
    import traceback
    traceback.print_exc()