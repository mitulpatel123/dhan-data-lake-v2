#!/usr/bin/env python3
"""
Comprehensive test suite for the Trading Universe Manager
This validates the complete F&O universe discovery system
"""

print("🧪 Testing Trading Universe Discovery System...")
print("=" * 70)

try:
    from core.universe_manager import universe_manager, IndexType, InstrumentClass
    print("✅ Universe manager imported successfully")
    
    # Test 1: Basic universe discovery
    print("\n🔍 Step 1: Discovering Complete Trading Universe...")
    print("   This may take 30-60 seconds to analyze all instruments...")
    
    universe = universe_manager.discover_complete_universe()
    
    print(f"\n📊 Universe Discovery Results:")
    for category, instruments in universe.items():
        print(f"   {category.replace('_', ' ').title()}: {len(instruments):,}")
    
    # Test 2: Get statistics
    print(f"\n📈 Step 2: Generating Universe Statistics...")
    stats = universe_manager.get_universe_statistics(universe)
    
    print(f"\n📊 Detailed Statistics:")
    print(f"   Total Instruments: {stats.total_instruments:,}")
    print(f"   Index Spots: {stats.index_spots}")
    print(f"   Index Futures: {stats.index_futures:,}")
    print(f"   Index Options: {stats.index_options:,}")
    print(f"   Constituent Stocks: {stats.stocks}")
    print(f"   Stock Futures: {stats.stock_futures:,}")
    print(f"   Stock Options: {stats.stock_options:,}")
    print(f"   Active Expiries: {len(stats.active_expiries)}")
    
    if stats.active_expiries:
        print(f"   Next 5 Expiries: {stats.active_expiries[:5]}")
    
    # Test 3: Get security IDs for API usage
    print(f"\n🔢 Step 3: Extracting Security IDs for API Usage...")
    security_ids = universe_manager.get_security_ids_by_category(universe)
    
    print(f"\n📋 Security ID Categories:")
    for category, ids in security_ids.items():
        print(f"   {category.replace('_', ' ').title()}: {len(ids):,} IDs")
    
    # Test 4: Show sample instruments from each category
    print(f"\n📝 Step 4: Sample Instruments by Category:")
    
    categories_to_sample = ['index_spots', 'index_futures', 'index_options', 
                          'stocks', 'stock_futures', 'stock_options']
    
    for category in categories_to_sample:
        instruments = universe.get(category, [])
        if instruments:
            sample = instruments[:3]  # First 3 instruments
            print(f"\n   {category.replace('_', ' ').title()} (showing 3 of {len(instruments)}):")
            for inst in sample:
                security_id = inst.get('SECURITY_ID', 'N/A')
                symbol = inst.get('SYMBOL_NAME', 'N/A')
                display = inst.get('DISPLAY_NAME', 'N/A')
                expiry = inst.get('SM_EXPIRY_DATE')
                expiry_str = expiry.strftime('%Y-%m-%d') if expiry else 'N/A'
                
                print(f"      ID {security_id}: {symbol} | {display} | Exp: {expiry_str}")
    
    # Test 5: Health validation
    print(f"\n🏥 Step 5: Universe Health Validation...")
    health = universe_manager.validate_universe_health(universe)
    
    print(f"\n💚 Health Check Results:")
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
    
    # Test 6: Validate constituent coverage
    print(f"\n🔍 Step 6: Validating Index Constituent Coverage...")
    
    # Check if we found the major indices
    index_spots = universe.get('index_spots', [])
    found_indices = {inst['SYMBOL_NAME'] for inst in index_spots}
    expected_indices = {'NIFTY 50', 'NIFTY BANK', 'NIFTY FIN SERVICE'}
    
    print(f"   Expected Indices: {expected_indices}")
    print(f"   Found Indices: {found_indices}")
    
    if expected_indices.issubset(found_indices):
        print(f"   ✅ All major indices found!")
    else:
        missing = expected_indices - found_indices
        print(f"   ❌ Missing indices: {missing}")
    
    # Check constituent stock coverage
    stocks = universe.get('stocks', [])
    found_stocks = {inst['SYMBOL_NAME'] for inst in stocks}
    
    nifty_50_found = len(found_stocks & universe_manager.NIFTY_50_CONSTITUENTS)
    bank_nifty_found = len(found_stocks & universe_manager.BANK_NIFTY_CONSTITUENTS)
    fin_nifty_found = len(found_stocks & universe_manager.FIN_NIFTY_CONSTITUENTS)
    
    print(f"\n   📈 Constituent Stock Coverage:")
    print(f"      Nifty 50: {nifty_50_found}/{len(universe_manager.NIFTY_50_CONSTITUENTS)} ({nifty_50_found/len(universe_manager.NIFTY_50_CONSTITUENTS)*100:.1f}%)")
    print(f"      Bank Nifty: {bank_nifty_found}/{len(universe_manager.BANK_NIFTY_CONSTITUENTS)} ({bank_nifty_found/len(universe_manager.BANK_NIFTY_CONSTITUENTS)*100:.1f}%)")
    print(f"      Fin Nifty: {fin_nifty_found}/{len(universe_manager.FIN_NIFTY_CONSTITUENTS)} ({fin_nifty_found/len(universe_manager.FIN_NIFTY_CONSTITUENTS)*100:.1f}%)")
    
    # Test 7: F&O Coverage Analysis
    print(f"\n📊 Step 7: F&O Coverage Analysis...")
    
    total_fo = (stats.index_futures + stats.index_options + 
                stats.stock_futures + stats.stock_options)
    fo_percentage = (total_fo / stats.total_instruments) * 100
    
    print(f"   Total F&O Contracts: {total_fo:,}")
    print(f"   F&O Coverage: {fo_percentage:.1f}% of total instruments")
    
    # Index F&O breakdown
    index_fo = stats.index_futures + stats.index_options
    print(f"   Index F&O: {index_fo:,} ({stats.index_futures:,} futures + {stats.index_options:,} options)")
    
    # Stock F&O breakdown  
    stock_fo = stats.stock_futures + stats.stock_options
    print(f"   Stock F&O: {stock_fo:,} ({stats.stock_futures:,} futures + {stats.stock_options:,} options)")
    
    # Final summary
    print(f"\n🎉 UNIVERSE DISCOVERY SUMMARY:")
    print(f"=" * 50)
    print(f"✅ Discovery Status: {'SUCCESS' if health['status'] == 'healthy' else 'ISSUES DETECTED'}")
    print(f"📊 Total Coverage: {stats.total_instruments:,} instruments")
    print(f"🎯 F&O Focus: {total_fo:,} F&O contracts ready for trading")
    print(f"📈 Index Coverage: 3 major indices + {index_fo:,} F&O contracts")
    print(f"📈 Stock Coverage: {stats.stocks} stocks + {stock_fo:,} F&O contracts")
    print(f"⏰ Active Expiries: {len(stats.active_expiries)} expiry cycles")
    
    if health['status'] == 'healthy':
        print(f"\n🚀 READY FOR DATA INGESTION!")
        print(f"   - Real-time WebSocket feed can track {total_fo:,} F&O contracts")
        print(f"   - Historical data fetcher can backfill all instruments")
        print(f"   - Option chain API can track {stats.index_options + stats.stock_options:,} options")
        print(f"   - Complete algorithmic trading infrastructure is ready!")
    else:
        print(f"\n⚠️ Please address health check issues before proceeding")

except Exception as e:
    print(f"❌ Universe discovery test FAILED: {e}")
    import traceback
    traceback.print_exc()
    
    print(f"\n🔧 Troubleshooting:")
    print(f"   1. Ensure instrument master sync completed successfully")
    print(f"   2. Check MongoDB connection and collections")
    print(f"   3. Verify instrument data quality and completeness")
    print(f"   4. Check for any import or dependency issues")