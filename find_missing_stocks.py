#!/usr/bin/env python3
"""
Script to find the correct full company names for the missing major stocks
based on display names and partial matches
"""

print("🔍 Finding Missing Major Stocks...")
print("=" * 60)

try:
    from database.collections import get_instruments_master
    
    collection = get_instruments_master()
    
    # Missing stocks that we need to find
    missing_stocks = {
        'TCS': ['TCS', 'TATA CONSULTANCY', 'CONSULTANCY'],
        'HDFCBANK': ['HDFC BANK', 'HDFCBANK'],
        'BHARTIARTL': ['BHARTI', 'AIRTEL'],
        'HINDUNILVR': ['HINDUSTAN UNILEVER', 'UNILEVER', 'HUL'],
        'LT': ['LARSEN', 'TOUBRO', 'L&T'],
        'SUNPHARMA': ['SUN PHARMA', 'SUN PHARMACEUTICAL'],
        'HCLTECH': ['HCL TECH', 'HCL TECHNOLOGIES'],
        'BAJFINANCE': ['BAJAJ FINANCE'],
        'MARUTI': ['MARUTI SUZUKI'],
        'KOTAKBANK': ['KOTAK', 'KOTAK MAHINDRA BANK'],
        'ULTRACEMCO': ['ULTRATECH', 'CEMENT'],
        'AXISBANK': ['AXIS BANK'],
        'NTPC': ['NTPC'],
        'ASIANPAINT': ['ASIAN PAINTS'],
        'NESTLEIND': ['NESTLE'],
        'BAJAJFINSV': ['BAJAJ FINSERV'],
        'ONGC': ['OIL AND NATURAL GAS', 'ONGC'],
        'M&M': ['MAHINDRA', 'M&M'],
        'TATASTEEL': ['TATA STEEL'],
        'TITAN': ['TITAN'],
        'POWERGRID': ['POWER GRID'],
        'COALINDIA': ['COAL INDIA'],
        'ADANIPORTS': ['ADANI PORT', 'ADANI PORTS'],
        'WIPRO': ['WIPRO'],
        'TATAMOTORS': ['TATA MOTORS'],
        'APOLLOHOSP': ['APOLLO HOSPITAL'],
        'DIVISLAB': ['DIVI', 'LABORATORIES'],
        'EICHERMOT': ['EICHER MOTOR'],
        'JSWSTEEL': ['JSW STEEL'],
        'BPCL': ['BHARAT PETROLEUM'],
        'TATACONSUM': ['TATA CONSUMER'],
        'TECHM': ['TECH MAHINDRA'],
        'GRASIM': ['GRASIM'],
        'HINDALCO': ['HINDALCO'],
        'SBILIFE': ['SBI LIFE'],
        'HEROMOTOCO': ['HERO MOTOCORP', 'HERO MOTO'],
        'INDUSINDBK': ['INDUSIND BANK'],
        'CIPLA': ['CIPLA'],
        'HDFCLIFE': ['HDFC LIFE'],
        'LTIM': ['LTI', 'MINDTREE'],
        'DRREDDY': ['DR REDDY', 'REDDY'],
        'BRITANNIA': ['BRITANNIA'],
        'TRENT': ['TRENT']
    }
    
    found_stocks = {}
    
    for expected_symbol, search_terms in missing_stocks.items():
        print(f"\n🔍 Searching for {expected_symbol}:")
        
        found = False
        for search_term in search_terms:
            if found:
                break
                
            # Search in SYMBOL_NAME
            results = list(collection.find({
                'INSTRUMENT': 'EQUITY',
                'SERIES': 'EQ',
                'SYMBOL_NAME': {'$regex': search_term, '$options': 'i'}
            }).limit(3))
            
            if results:
                print(f"   Found in SYMBOL_NAME with '{search_term}':")
                for result in results:
                    symbol = result.get('SYMBOL_NAME', 'N/A')
                    display = result.get('DISPLAY_NAME', 'N/A')
                    sec_id = result.get('SECURITY_ID', 'N/A')
                    print(f"      ID {sec_id}: '{symbol}' | Display: '{display}'")
                    
                    if not found:
                        found_stocks[expected_symbol] = symbol
                        found = True
                continue
            
            # Search in DISPLAY_NAME
            results = list(collection.find({
                'INSTRUMENT': 'EQUITY',  
                'SERIES': 'EQ',
                'DISPLAY_NAME': {'$regex': search_term, '$options': 'i'}
            }).limit(3))
            
            if results:
                print(f"   Found in DISPLAY_NAME with '{search_term}':")
                for result in results:
                    symbol = result.get('SYMBOL_NAME', 'N/A')
                    display = result.get('DISPLAY_NAME', 'N/A')
                    sec_id = result.get('SECURITY_ID', 'N/A')
                    print(f"      ID {sec_id}: '{symbol}' | Display: '{display}'")
                    
                    if not found:
                        found_stocks[expected_symbol] = symbol
                        found = True
                break
        
        if not found:
            print(f"   ❌ No matches found for {expected_symbol}")
    
    # Generate updated constituent lists
    print(f"\n💡 FOUND STOCKS SUMMARY:")
    print(f"=" * 50)
    print(f"Found {len(found_stocks)} out of {len(missing_stocks)} missing stocks:")
    
    for expected, actual in found_stocks.items():
        print(f"   {expected} → '{actual}'")
    
    # Generate the complete updated list
    print(f"\n📝 UPDATED CONSTITUENT LISTS:")
    print(f"=" * 50)
    
    print("# Add these to your universe manager NIFTY_50_CONSTITUENTS:")
    base_stocks = {
        'RELIANCE INDUSTRIES LTD', 'INFOSYS LIMITED', 'ITC LTD'
    }
    
    all_found = base_stocks.union(set(found_stocks.values()))
    
    print("NIFTY_50_CONSTITUENTS = {")
    for stock in sorted(all_found):
        print(f"    '{stock}',")
    print("}")
    
    # Also search for Bank Nifty and Fin Nifty stocks
    print(f"\n🏦 Searching for Bank Stocks...")
    
    bank_search_terms = {
        'HDFC BANK': ['HDFC BANK'],
        'ICICI BANK': ['ICICI BANK'],
        'STATE BANK': ['STATE BANK', 'SBI'],
        'KOTAK BANK': ['KOTAK MAHINDRA', 'KOTAK BANK'],
        'AXIS BANK': ['AXIS BANK'],
        'INDUSIND BANK': ['INDUSIND BANK']
    }
    
    found_banks = {}
    for bank_name, terms in bank_search_terms.items():
        for term in terms:
            result = collection.find_one({
                'INSTRUMENT': 'EQUITY',
                'SERIES': 'EQ',
                '$or': [
                    {'SYMBOL_NAME': {'$regex': term, '$options': 'i'}},
                    {'DISPLAY_NAME': {'$regex': term, '$options': 'i'}}
                ]
            })
            
            if result:
                symbol = result.get('SYMBOL_NAME', 'N/A')
                display = result.get('DISPLAY_NAME', 'N/A')
                sec_id = result.get('SECURITY_ID', 'N/A')
                print(f"   ✅ {bank_name}: '{symbol}' (ID: {sec_id}) | Display: '{display}'")
                found_banks[bank_name] = symbol
                break
    
    print(f"\n🎯 NEXT STEPS:")
    print(f"=" * 50)
    print(f"1. Update the universe manager with the found symbols above")
    print(f"2. Test the universe manager again")
    print(f"3. If results are good, proceed with historical data fetcher")

except Exception as e:
    print(f"❌ Missing stock search failed: {e}")
    import traceback
    traceback.print_exc()