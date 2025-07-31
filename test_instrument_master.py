#!/usr/bin/env python3
"""
Test script for the Instrument Master Fetcher
This will download and sync the complete instrument list
"""

print("🧪 Testing Instrument Master Pipeline...")
print("=" * 60)

try:
    from data_fetchers.instrument_master import instrument_fetcher
    print("✅ Instrument master fetcher imported successfully")
    
    # Run the complete daily sync process
    print("\n🚀 Running daily instrument master sync...")
    print("   This may take 30-60 seconds to download and process all instruments...")
    
    results = instrument_fetcher.run_daily_sync()
    
    # Display results
    print(f"\n📊 Sync Results:")
    print(f"   Status: {results['status'].upper()}")
    print(f"   Duration: {results['duration_seconds']}s")
    
    if results['status'] == 'success':
        print(f"   Raw CSV Records: {results['raw_count']:,}")
        print(f"   Cleaned Records: {results['cleaned_count']:,}")
        
        sync_stats = results['sync_stats']
        print(f"   MongoDB Upserted: {sync_stats['upserted']:,}")
        print(f"   MongoDB Modified: {sync_stats['modified']:,}")
        print(f"   MongoDB Errors: {sync_stats['errors']:,}")
        
        validation = results['validation']
        print(f"\n🔍 Validation Results:")
        print(f"   Total Instruments: {validation['total_instruments']:,}")
        print(f"   Active F&O Contracts: {validation['active_fo_contracts']:,}")
        print(f"   Coverage Ratio: {validation['coverage_ratio']:.1%}")
        
        print(f"\n📈 Instruments by Type:")
        by_type = validation['by_instrument_type']
        for instrument_type, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   {instrument_type}: {count:,}")
        
        # Show some sample instruments
        print(f"\n📋 Sample Instruments:")
        from database.collections import get_instruments_master
        collection = get_instruments_master()
        
        # Sample of different types
        samples = [
            ("Nifty Index", {"SYMBOL_NAME": "NIFTY 50"}),
            ("Bank Nifty Index", {"SYMBOL_NAME": "NIFTY BANK"}),
            ("Sample Stock", {"INSTRUMENT": "EQUITY", "SERIES": "EQ"}),
            ("Sample Future", {"INSTRUMENT": "FUTSTK"}),
            ("Sample Option", {"INSTRUMENT": "OPTSTK"})
        ]
        
        for sample_name, query in samples:
            sample_doc = collection.find_one(query)
            if sample_doc:
                print(f"   {sample_name}: {sample_doc['DISPLAY_NAME']} (ID: {sample_doc['SECURITY_ID']})")
        
        print(f"\n🎉 SUCCESS! Instrument master is now loaded and ready.")
        print(f"💡 This data will be used to discover F&O contracts for:")
        print(f"   - Nifty 50, Bank Nifty, Fin Nifty indices")
        print(f"   - All constituent stocks")
        print(f"   - All active futures and options contracts")
        
    else:
        print(f"   Error: {results.get('error', 'Unknown error')}")
        print(f"\n❌ Instrument master sync failed. Check the error above.")

except Exception as e:
    print(f"❌ Test FAILED: {e}")
    import traceback
    traceback.print_exc()
    
    print(f"\n🔧 Troubleshooting:")
    print(f"   1. Check internet connectivity")
    print(f"   2. Verify MongoDB is accessible")
    print(f"   3. Ensure collections are properly set up")