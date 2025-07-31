#!/usr/bin/env python3
"""
Quick test script to verify configuration is working
"""

print("🧪 Testing DhanHQ Data Lake Configuration...")
print("=" * 50)

try:
    # Test import
    from config.settings import config
    print("✅ Configuration imported successfully")
    
    # Test health check
    health = config.health_check()
    print("\n📊 Configuration Health Check:")
    for key, value in health.items():
        print(f"   {key}: {value}")
    
    # Test credential access
    print("\n🔑 API Credentials Test:")
    firehose_creds = config.get_firehose_credentials()
    workhorse_creds = config.get_workhorse_credentials()
    
    print(f"   Firehose Client ID: {firehose_creds['client_id'][:8]}..." if firehose_creds['client_id'] else "   Firehose Client ID: NOT SET")
    print(f"   Workhorse Client ID: {workhorse_creds['client_id'][:8]}..." if workhorse_creds['client_id'] else "   Workhorse Client ID: NOT SET")
    
    # Test MongoDB config
    print(f"\n🗄️ MongoDB Configuration:")
    print(f"   Database: {config.mongo_db_name}")
    print(f"   URI configured: {'Yes' if config.mongo_uri else 'No'}")
    
    print("\n✅ Configuration test PASSED!")
    
    # Optional: Test API connections (uncomment if you want to test actual API calls)
    # print("\n🔌 Testing API Connections...")
    # api_test = config.test_api_connection()
    # for client, result in api_test.items():
    #     status = result['status']
    #     error = result.get('error', '')
    #     print(f"   {client}: {status} {('- ' + str(error)) if error else ''}")

except Exception as e:
    print(f"❌ Configuration test FAILED: {e}")
    import traceback
    traceback.print_exc()