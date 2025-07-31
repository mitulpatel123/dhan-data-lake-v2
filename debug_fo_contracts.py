#!/usr/bin/env python3
"""
Debug script to understand why F&O contracts are not being discovered
This will help us fix the universe manager F&O discovery logic
"""

print("🔍 Debugging F&O Contract Discovery...")
print("=" * 60)

try:
    from database.collections import get_instruments_master
    from datetime import datetime, timezone
    
    collection = get_instruments_master()
    
    # 1. Check total F&O instruments in database
    print("\n📊 Step 1: F&O Instruments Overview...")
    
    fo_types = ['FUTIDX', 'OPTIDX', 'FUTSTK', 'OPTSTK']
    
    for fo_type in fo_types:
        count = collection.count_documents({'INSTRUMENT': fo_type})
        print(f"   {fo_type}: {count:,} instruments")
    
    total_fo = sum(collection.count_documents({'INSTRUMENT': fo_type}) for fo_type in fo_types)
    print(f"   Total F&O: {total_fo:,} instruments")
    
    # 2. Check what underlying security IDs exist for our indices
    print(f"\n🎯 Step 2: Index Underlying Security ID Check...")
    
    # Get our major indices
    major_indices = [2, 13, 25, 27]  # IDs found in test
    
    for idx_id in major_indices:
        index_info = collection.find_one({'SECURITY_ID': idx_id})
        if index_info:
            symbol = index_info.get('SYMBOL_NAME', 'N/A')
            display = index_info.get('DISPLAY_NAME', 'N/A')
            print(f"\n   Index ID {idx_id}: '{symbol}' | Display: '{display}'")
            
            # Look for F&O contracts with this as underlying
            for fo_type in ['FUTIDX', 'OPTIDX']:
                fo_count = collection.count_documents({
                    'INSTRUMENT': fo_type,
                    'UNDERLYING_SECURITY_ID': idx_id
                })
                print(f"      {fo_type} contracts: {fo_count:,}")
                
                # Show sample contracts
                if fo_count > 0:
                    samples = list(collection.find({
                        'INSTRUMENT': fo_type,
                        'UNDERLYING_SECURITY_ID': idx_id
                    }).limit(3))
                    
                    for sample in samples:
                        sec_id = sample.get('SECURITY_ID', 'N/A')
                        symbol = sample.get('SYMBOL_NAME', 'N/A')
                        expiry = sample.get('SM_EXPIRY_DATE', 'N/A')
                        print(f"         Sample: ID {sec_id}: '{symbol}' | Expiry: {expiry}")
    
    # 3. Check expiry date format and filtering
    print(f"\n📅 Step 3: Expiry Date Analysis...")
    
    # Sample F&O contracts to understand expiry date format
    sample_fo = list(collection.find(
        {'INSTRUMENT': {'$in': fo_types}},
        {'SECURITY_ID': 1, 'SYMBOL_NAME': 1, 'SM_EXPIRY_DATE': 1, 'INSTRUMENT': 1}
    ).limit(10))
    
    print(f"Sample F&O contracts with expiry dates:")
    today = datetime.now(timezone.utc)
    print(f"Today's date for comparison: {today}")
    
    for sample in sample_fo:
        sec_id = sample.get('SECURITY_ID', 'N/A')
        symbol = sample.get('SYMBOL_NAME', 'N/A')
        expiry = sample.get('SM_EXPIRY_DATE', 'N/A')
        instrument = sample.get('INSTRUMENT', 'N/A')
        
        # Check if expiry is in future
        is_active = "Unknown"
        if expiry and expiry != 'N/A':
            if isinstance(expiry, datetime):
                is_active = "Active" if expiry >= today else "Expired"
            else:
                is_active = f"Format: {type(expiry)}"
        
        print(f"   ID {sec_id}: {instrument} '{symbol}' | Expiry: {expiry} | Status: {is_active}")
    
    # 4. Test the active contract filter logic
    print(f"\n🔍 Step 4: Testing Active Contract Filter...")
    
    # Try different filter approaches
    filters = [
        # Current filter (from universe manager)
        {
            '$or': [
                {'SM_EXPIRY_DATE': {'$gte': today}},
                {'SM_EXPIRY_DATE': None}
            ]
        },
        # Alternative filter - check for non-null expiry dates first
        {
            'SM_EXPIRY_DATE': {'$ne': None}
        },
        # No date filter (get all)
        {}
    ]
    
    for i, date_filter in enumerate(filters, 1):
        print(f"\n   Filter {i}: {date_filter}")
        
        for fo_type in ['FUTIDX', 'OPTIDX']:
            query = {
                'INSTRUMENT': fo_type,
                'UNDERLYING_SECURITY_ID': {'$in': major_indices},
                **date_filter
            }
            
            count = collection.count_documents(query)
            print(f"      {fo_type} with filter: {count:,}")
            
            if count > 0:
                # Show a sample
                sample = collection.find_one(query)
                if sample:
                    sec_id = sample.get('SECURITY_ID', 'N/A')
                    symbol = sample.get('SYMBOL_NAME', 'N/A')
                    expiry = sample.get('SM_EXPIRY_DATE', 'N/A')
                    underlying = sample.get('UNDERLYING_SECURITY_ID', 'N/A')
                    print(f"         Sample: ID {sec_id}: '{symbol}' | Underlying: {underlying} | Expiry: {expiry}")
    
    # 5. Check if issue is with underlying symbol vs security ID
    print(f"\n🔍 Step 5: Checking Underlying Symbol vs Security ID...")
    
    # Look for F&O contracts using UNDERLYING_SYMBOL instead
    index_symbols = ['NIFTY', 'BANKNIFTY', 'NIFTY FIN SERVICE']
    
    for symbol in index_symbols:
        print(f"\n   Looking for F&O with UNDERLYING_SYMBOL = '{symbol}':")
        
        for fo_type in ['FUTIDX', 'OPTIDX']:
            count = collection.count_documents({
                'INSTRUMENT': fo_type,
                'UNDERLYING_SYMBOL': symbol
            })
            print(f"      {fo_type}: {count:,}")
            
            if count > 0:
                sample = collection.find_one({
                    'INSTRUMENT': fo_type,
                    'UNDERLYING_SYMBOL': symbol
                })
                if sample:
                    sec_id = sample.get('SECURITY_ID', 'N/A')
                    sample_symbol = sample.get('SYMBOL_NAME', 'N/A')
                    expiry = sample.get('SM_EXPIRY_DATE', 'N/A')
                    print(f"         Sample: ID {sec_id}: '{sample_symbol}' | Expiry: {expiry}")
    
    # 6. Summary and recommendations
    print(f"\n💡 SUMMARY & RECOMMENDATIONS:")
    print(f"=" * 60)
    
    if total_fo == 0:
        print(f"❌ No F&O data in database - check instrument master sync")
    elif total_fo > 0:
        print(f"✅ F&O data exists: {total_fo:,} total contracts")
        print(f"🔧 Issue likely in:")
        print(f"   1. Underlying Security ID mapping")
        print(f"   2. Expiry date filtering logic")
        print(f"   3. UNDERLYING_SYMBOL vs UNDERLYING_SECURITY_ID usage")
        
        print(f"\n📝 Next steps:")
        print(f"   1. Update universe manager based on findings above")
        print(f"   2. Fix the underlying ID/symbol mapping issue")
        print(f"   3. Adjust expiry date filtering if needed")

except Exception as e:
    print(f"❌ F&O debug failed: {e}")
    import traceback
    traceback.print_exc()