#!/usr/bin/env python3
"""
Fix script to recreate the time-series collections that failed due to
MongoDB 8.0 compatibility issues with bucket parameters.
"""

print("🔧 Fixing Time-Series Collections...")
print("=" * 50)

try:
    from database.collections import collections
    
    # Collections that need to be recreated
    failed_collections = ['historical_ohlcv', 'live_tick_data']
    
    for collection_name in failed_collections:
        print(f"\n🔄 Recreating '{collection_name}'...")
        
        # Force recreate the collection
        try:
            result = collections.create_collection(collection_name, force_recreate=True)
            if result:
                print(f"✅ '{collection_name}' created successfully")
            else:
                print(f"⚠️ '{collection_name}' already existed (unexpected)")
        except Exception as e:
            print(f"❌ Failed to create '{collection_name}': {e}")
    
    # Validate all collections again
    print(f"\n🔍 Validating all collections...")
    validation = collections.validate_collections()
    
    print(f"📊 Validation Status: {validation['status'].upper()}")
    
    if validation['missing_collections']:
        print(f"❌ Still missing: {validation['missing_collections']}")
    else:
        print("✅ All collections are now present!")
    
    # Show final status
    print(f"\n📈 Final Collection Status:")
    for collection_name, info in validation['collections'].items():
        collection_type = info['type'].upper()
        print(f"   {collection_name}: {collection_type} ✅")
        
        if info.get('timeseries_config'):
            ts_config = info['timeseries_config']
            print(f"      ⏰ Time Field: {ts_config.get('timeField')}")
            print(f"      📊 Granularity: {ts_config.get('granularity')}")
    
    if validation['status'] == 'healthy':
        print(f"\n🎉 SUCCESS! All collections are now working properly.")
        print(f"📊 Ready for data ingestion!")

except Exception as e:
    print(f"❌ Fix script FAILED: {e}")
    import traceback
    traceback.print_exc()