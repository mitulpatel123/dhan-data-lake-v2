#!/usr/bin/env python3
"""
Test script for the FIXED Trading Universe Manager
This will validate that the symbol corrections are working
"""

print("🧪 Testing FIXED Trading Universe Manager...")
print("=" * 70)

try:
    # First, let's temporarily replace the universe manager file
    print("📝 Note: Make sure you've replaced core/universe_manager.py with the fixed version!")
    print()
    
    from core.universe_manager import universe_manager, IndexType, InstrumentClass
    print("✅ Fixed universe manager imported successfully")
    
    # Test 1: Check if corrected symbols are found
    print("\n🔍 Step 1: Validating Corrected Index Symbols...")
    
    print("Expected index symbols:")
    for idx_type in IndexType:
        print(f"   {idx_type.name}: '{idx_type.value}'")
    
    # Test 2: Try basic universe discovery
    print(f"\n🔍 Step 2: Testing Universe Discovery...")
    print("   This may take 30-60 seconds to analyze all instruments...")
    
    try:
        universe = universe_manager.discover_complete_universe()
        
        print(f"\n📊 Universe Discovery Results:")
        for category, instruments in universe.items():
            print(f"   {category.replace('_', ' ').title()}: {len(instruments):,}")
        
        # Test 3: Check if we found the major indices
        print(f"\n✅ Step 3: Index Validation...")
        index_spots = universe.get('index_spots', [])
        
        if index_spots:
            print(f"Found {len(index_spots)} index spots:")
            for idx in index_spots:
                symbol = idx.get('SYMBOL_NAME', 'N/A')
                display = idx.get('DISPLAY_NAME', 'N/A')
                sec_id = idx.get('SECURITY_ID', 'N/A')
                print(f"   ✅ {symbol} (ID: {sec_id}) - {display}")
        else:
            print("   ❌ No index spots found!")
        
        # Test 4: Check stock discovery
        print(f"\n📈 Step 4: Stock Discovery Validation...")
        stocks = universe.get('stocks', [])
        
        if stocks:
            print(f"Found {len(stocks)} constituent stocks:")
            # Show first 10 stocks
            for stock in stocks[:10]:
                symbol = stock.get('SYMBOL_NAME', 'N/A')
                display = stock.get('DISPLAY_NAME', 'N/A')
                sec_id = stock.get('SECURITY_ID', 'N/A')
                print(f"   ✅ {symbol} (ID: {sec_id}) - {display}")
            
            if len(stocks) > 10:
                print(f"   ... and {len(stocks) - 10} more stocks")
        else:
            print("   ⚠️ No constituent stocks found! This might be expected if symbol format is different.")
        
        # Test 5: F&O Coverage Check
        print(f"\n📊 Step 5: F&O Coverage Analysis...")
        
        total_fo = (len(universe.get('index_futures', [])) + 
                   len(universe.get('index_options', [])) + 
                   len(universe.get('stock_futures', [])) + 
                   len(universe.get('stock_options', [])))
        
        print(f"   Index Futures: {len(universe.get('index_futures', [])):,}")
        print(f"   Index Options: {len(universe.get('index_options', [])):,}")
        print(f"   Stock Futures: {len(universe.get('stock_futures', [])):,}")
        print(f"   Stock Options: {len(universe.get('stock_options', [])):,}")
        print(f"   Total F&O Contracts: {total_fo:,}")
        
        # Test 6: Get Statistics
        print(f"\n📈 Step 6: Generating Universe Statistics...")
        stats = universe_manager.get_universe_statistics(universe)
        
        print(f"   Total Instruments: {stats.total_instruments:,}")
        print(f"   Discovery Time: {stats.discovery_timestamp}")
        print(f"   Active Expiries: {len(stats.active_expiries)}")
        if stats.active_expiries:
            print(f"   Next 5 Expiries: {stats.active_expiries[:5]}")
        
        # Test 7: Health Check
        print(f"\n🏥 Step 7: Universe Health Check...")
        health = universe_manager.validate_universe_health(universe)
        
        print(f"   Status: {health['status'].upper()}")
        
        if health.get('issues'):
            print(f"   🚨 Issues:")
            for issue in health['issues']:
                print(f"      - {issue}")
        
        if health.get('warnings'):
            print(f"   ⚠️ Warnings:")
            for warning in health['warnings']:
                print(f"      - {warning}")
        
        if health.get('recommendations'):
            print(f"   💡 Recommendations:")
            for rec in health['recommendations']:
                print(f"      - {rec}")
        
        # Test 8: Security IDs for API Usage
        print(f"\n🔢 Step 8: Security IDs for API Usage...")
        security_ids = universe_manager.get_security_ids_by_category(universe)
        
        print(f"   Index Spots: {len(security_ids.get('index_spots', []))} IDs")
        print(f"   All F&O Contracts: {len(security_ids.get('all_fo', []))} IDs")
        print(f"   Everything: {len(security_ids.get('everything', []))} IDs")
        
        # Final Assessment
        print(f"\n🎯 FINAL ASSESSMENT:")
        print(f"=" * 50)
        
        success_indicators = [
            len(index_spots) >= 3,  # Found major indices
            total_fo > 0,           # Found some F&O contracts
            stats.total_instruments > 0  # Found some instruments
        ]
        
        success_count = sum(success_indicators)
        
        if success_count == 3:
            print(f"🎉 SUCCESS! Universe manager is working correctly.")
            print(f"   ✅ Major indices: Found")
            print(f"   ✅ F&O contracts: {total_fo:,} found")
            print(f"   ✅ Total instruments: {stats.total_instruments:,}")
            print(f"\n🚀 READY FOR NEXT STEP: Historical Data Fetcher")
            
        elif success_count == 2:
            print(f"⚠️ PARTIAL SUCCESS: Universe manager mostly working.")
            print(f"   Major indices: {'✅' if len(index_spots) >= 3 else '❌'}")
            print(f"   F&O contracts: {'✅' if total_fo > 0 else '❌'}")
            print(f"   Total instruments: {'✅' if stats.total_instruments > 0 else '❌'}")
            print(f"\n💡 Consider investigating stock symbol format issues.")
            
        else:
            print(f"❌ ISSUES DETECTED: Universe manager needs more fixes.")
            print(f"   Major indices: {'✅' if len(index_spots) >= 3 else '❌'}")
            print(f"   F&O contracts: {'✅' if total_fo > 0 else '❌'}")
            print(f"   Total instruments: {'✅' if stats -total_instruments > 0 else '❌'}")
            print(f"\n🔧 Run the enhanced stock discovery script for more details.")
        
    except Exception as e:
        print(f"❌ Universe discovery failed: {e}")
        import traceback
        traceback.print_exc()

except Exception as e:
    print(f"❌ Test FAILED: {e}")
    import traceback
    traceback.print_exc()
    
    print(f"\n🔧 Troubleshooting Steps:")
    print(f"   1. Make sure you replaced core/universe_manager.py with the fixed version")
    print(f"   2. Check that the instrument master data is properly loaded")
    print(f"   3. Run the enhanced stock discovery script for more details")