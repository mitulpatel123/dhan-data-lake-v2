#!/usr/bin/env python3
"""
Debug script to examine the CSV structure and fix column mapping issues
"""

import pandas as pd
import requests

print("🔍 Debugging CSV Structure...")
print("=" * 50)

try:
    # Download the CSV
    url = "https://images.dhan.co/api-data/api-scrip-master-detailed.csv"
    print(f"📥 Downloading CSV from: {url}")
    
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    
    print(f"✅ Downloaded {len(response.content)} bytes")
    
    # Parse just the first few rows to examine structure
    df = pd.read_csv(
        pd.io.common.StringIO(response.text),
        dtype=str,
        nrows=10  # Only read first 10 rows for debugging
    )
    
    print(f"\n📋 CSV Structure:")
    print(f"   Total columns: {len(df.columns)}")
    print(f"   Shape: {df.shape}")
    
    print(f"\n📊 Column Names:")
    for i, col in enumerate(df.columns):
        print(f"   {i+1:2d}. {col}")
    
    print(f"\n📝 Sample Data (first 3 rows):")
    print(df.head(3).to_string())
    
    # Look for key columns we need
    key_columns = {
        'Security ID': ['SEM_EXM_EXCH_ID', 'SECURITY_ID', 'securityId'],
        'Symbol': ['SM_SYMBOL_NAME', 'SYMBOL_NAME', 'symbol'],
        'Display Name': ['SEM_CUSTOM_SYMBOL', 'DISPLAY_NAME', 'displayName'],
        'Instrument': ['SEM_INSTRUMENT_NAME', 'INSTRUMENT', 'instrument'],
        'Expiry Date': ['SEM_EXPIRY_DATE', 'SM_EXPIRY_DATE', 'expiryDate']
    }
    
    print(f"\n🔍 Key Column Mapping:")
    for key_name, possible_cols in key_columns.items():
        found_col = None
        for col in possible_cols:
            if col in df.columns:
                found_col = col
                break
        
        if found_col:
            print(f"   ✅ {key_name}: Found as '{found_col}'")
            # Show sample values
            sample_values = df[found_col].dropna().head(3).tolist()
            print(f"      Sample values: {sample_values}")
        else:
            print(f"   ❌ {key_name}: NOT FOUND in {possible_cols}")
    
    # Check for instruments that look like F&O
    if 'SEM_INSTRUMENT_NAME' in df.columns:
        instrument_types = df['SEM_INSTRUMENT_NAME'].value_counts()
        print(f"\n📈 Instrument Types Found:")
        for inst_type, count in instrument_types.head(10).items():
            print(f"   {inst_type}: {count}")

except Exception as e:
    print(f"❌ Debug failed: {e}")
    import traceback
    traceback.print_exc()