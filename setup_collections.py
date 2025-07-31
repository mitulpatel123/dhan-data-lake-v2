#!/usr/bin/env python3
"""
Collection Setup Script for DhanHQ Data Lake

This script creates all required MongoDB collections with proper
time-series configurations and indexing for optimal performance.
"""

print("🏗️ Setting up DhanHQ Data Lake Collections...")
print("=" * 60)

try:
    # Import collection manager
    from database.collections import collections
    print("✅ Collection manager imported successfully")
    
    # Show current status
    print("\n📊 Current Database Status:")
    current_collections = collections.db.list_collection_names()
    print(f"   Existing collections: {len(current_collections)}")
    if current_collections:
        print(f"   Collection names: {current_collections}")
    
    # Create all collections
    print("\n🏗️ Creating all required collections...")
    results = collections.create_all_collections(force_recreate=False)
    
    print("\n📋 Collection Creation Results:")
    for collection_name, created in results.items():
        status = "✅ CREATED" if created else "⚠️ EXISTS"
        config = collections.collection_configs[collection_name]
        collection_type = config['type'].upper()
        description = config['description']
        
        print(f"   {collection_name}: {status}")
        print(f"      Type: {collection_type}")
        print(f"      Description: {description}")
        
        if config['type'] == 'timeseries':
            print(f"      Time Field: {config['time_field']}")
            print(f"      Granularity: {config['granularity']}")
        
        indexes = len(config.get('indexes', []))
        print(f"      Indexes: {indexes}")
        print()
    
    # Validate all collections
    print("🔍 Validating Collections...")
    validation = collections.validate_collections()
    
    print(f"📊 Validation Status: {validation['status'].upper()}")
    
    if validation['missing_collections']:
        print(f"❌ Missing Collections: {validation['missing_collections']}")
    else:
        print("✅ All required collections are present")
    
    # Show detailed collection info
    print("\n📈 Collection Details:")
    for collection_name, info in validation['collections'].items():
        print(f"   {collection_name}:")
        print(f"      Type: {info['type']}")
        print(f"      Documents: {info['document_count']}")
        print(f"      Size: {info['size_mb']}MB")
        print(f"      Indexes: {info['index_count']} ({', '.join(info['indexes'])})")
        
        if info.get('timeseries_config'):
            ts_config = info['timeseries_config']
            print(f"      Time-Series Config:")
            print(f"         Time Field: {ts_config.get('timeField', 'unknown')}")
            print(f"         Meta Field: {ts_config.get('metaField', 'unknown')}")
            print(f"         Granularity: {ts_config.get('granularity', 'unknown')}")
        print()
    
    # Show overall statistics
    print("📊 Overall Database Statistics:")
    stats = collections.get_collection_stats()
    print(f"   Database: {stats['database_name']}")
    print(f"   Total Collections: {stats['total_collections']}")
    print(f"   Total Documents: {stats['total_documents']}")
    print(f"   Total Size: {stats['total_size_mb']}MB")
    
    if validation['status'] == 'healthy':
        print("\n🎉 SUCCESS! All collections are set up and ready for data ingestion.")
        print("\n📝 Next Steps:")
        print("   1. ✅ Configuration is working")
        print("   2. ✅ MongoDB connection is established") 
        print("   3. ✅ Collections are created with proper indexing")
        print("   4. 🔄 Ready to build data fetchers and start ingesting data!")
    else:
        print("\n⚠️ Some issues were found. Please check the validation results above.")

except Exception as e:
    print(f"❌ Collection setup FAILED: {e}")
    import traceback
    traceback.print_exc()
    
    print(f"\n🔧 Troubleshooting:")
    print(f"   1. Ensure MongoDB connection is working")
    print(f"   2. Check that your MongoDB user has proper permissions")
    print(f"   3. Verify there's enough space in your MongoDB cluster")