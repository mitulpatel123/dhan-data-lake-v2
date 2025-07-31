#!/usr/bin/env python3
"""
Test script to verify MongoDB connection is working
"""

print("🧪 Testing MongoDB Connection...")
print("=" * 50)

try:
    # Test import
    from database.mongodb_handler import mongodb, CLIENT, DATABASE
    print("✅ MongoDB handler imported successfully")
    
    # Test basic connection info
    print(f"\n📊 Connection Info:")
    print(f"   Database: {DATABASE.name}")
    print(f"   Client connected: {CLIENT is not None}")
    
    # Test health check
    print("\n💚 Health Check:")
    health = mongodb.health_check()
    
    if health['status'] == 'healthy':
        conn_info = health['connection']
        db_info = health['database']
        
        print(f"   Status: {health['status']}")
        print(f"   Ping Time: {conn_info['ping_time_ms']}ms")
        print(f"   Server Version: {conn_info['server_version']}")
        print(f"   Pool Size: {conn_info['min_pool_size']}-{conn_info['max_pool_size']}")
        print(f"   Collections: {db_info['collections']}")
        print(f"   Data Size: {db_info['data_size_mb']}MB")
        print(f"   Index Size: {db_info['index_size_mb']}MB")
    else:
        print(f"   Status: {health['status']}")
        print(f"   Error: {health.get('error', 'Unknown error')}")
    
    # Test connection stats
    print("\n🔗 Connection Stats:")
    stats = mongodb.get_connection_stats()
    print(f"   Topology: {stats.get('topology_type', 'unknown')}")
    print(f"   Servers: {stats.get('servers', 0)}")
    
    # Test a simple operation
    print("\n🔍 Testing Basic Operations:")
    
    # List existing collections
    collections = DATABASE.list_collection_names()
    print(f"   Existing collections: {len(collections)}")
    if collections:
        print(f"   Collection names: {collections[:5]}{'...' if len(collections) > 5 else ''}")
    
    # Test write/read operation
    test_collection = DATABASE['test_connection']
    
    # Insert a test document
    test_doc = {
        'test': True,
        'timestamp': 'connection_test',
        'message': 'MongoDB connection working!'
    }
    
    result = test_collection.insert_one(test_doc)
    print(f"   Test document inserted: {result.inserted_id}")
    
    # Read the test document back
    found_doc = test_collection.find_one({'test': True})
    if found_doc:
        print(f"   Test document found: {found_doc['message']}")
    
    # Clean up test document
    test_collection.delete_one({'test': True})
    print(f"   Test document cleaned up")
    
    print("\n✅ MongoDB connection test PASSED!")
    print(f"🎉 Ready to create collections and start data ingestion!")

except Exception as e:
    print(f"❌ MongoDB connection test FAILED: {e}")
    import traceback
    traceback.print_exc()
    
    print(f"\n🔧 Troubleshooting tips:")
    print(f"   1. Check your MONGO_URI in .env file")
    print(f"   2. Ensure your MongoDB cluster is running") 
    print(f"   3. Verify network connectivity to MongoDB")
    print(f"   4. Check if your IP is whitelisted in MongoDB Atlas")