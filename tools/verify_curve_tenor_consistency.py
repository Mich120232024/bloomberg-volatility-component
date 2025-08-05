#!/usr/bin/env python3
"""
Verify all OIS curves have the same tenor structure as USD
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from yield_curve_db_endpoint import get_database_connection
import pandas as pd

def extract_tenor_from_ticker(ticker):
    """Extract tenor number from ticker like USSO1, USSO10, etc."""
    import re
    match = re.search(r'[A-Z]+O(\d+)', ticker)
    if match:
        return int(match.group(1))
    return None

def verify_tenor_consistency():
    """Check all curves have same tenor structure"""
    conn = get_database_connection()
    
    # Get all tickers from ticker_reference
    query = """
        SELECT 
            currency_code,
            bloomberg_ticker,
            curve_name
        FROM ticker_reference
        WHERE is_active = true
        ORDER BY currency_code, bloomberg_ticker
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    # Extract tenor numbers
    df['tenor_number'] = df['bloomberg_ticker'].apply(extract_tenor_from_ticker)
    
    # Group by currency and get tenor sets
    print("=== TENOR STRUCTURE BY CURRENCY ===\n")
    
    tenor_sets = {}
    for currency in sorted(df['currency_code'].unique()):
        currency_df = df[df['currency_code'] == currency]
        tenors = sorted(currency_df['tenor_number'].dropna().unique())
        tenor_sets[currency] = tenors
        
        print(f"{currency} ({currency_df['curve_name'].iloc[0]}):")
        print(f"  Tenors: {tenors}")
        print(f"  Tickers: {list(currency_df['bloomberg_ticker'])}\n")
    
    # Check consistency
    print("=== TENOR CONSISTENCY CHECK ===\n")
    
    usd_tenors = tenor_sets.get('USD', [])
    print(f"USD reference tenors: {usd_tenors}\n")
    
    all_consistent = True
    for currency, tenors in tenor_sets.items():
        if currency == 'USD':
            continue
            
        if tenors == usd_tenors:
            print(f"✅ {currency}: MATCHES USD tenor structure")
        else:
            print(f"❌ {currency}: DIFFERENT tenor structure")
            missing = set(usd_tenors) - set(tenors)
            extra = set(tenors) - set(usd_tenors)
            if missing:
                print(f"   Missing tenors: {sorted(missing)}")
            if extra:
                print(f"   Extra tenors: {sorted(extra)}")
            all_consistent = False
    
    print(f"\n{'✅ All curves have consistent tenor structure' if all_consistent else '❌ Tenor structures are inconsistent'}")
    
    # Show what tickers are needed for missing tenors
    if not all_consistent:
        print("\n=== MISSING TICKERS TO ADD ===")
        for currency, tenors in tenor_sets.items():
            if currency == 'USD' or tenors == usd_tenors:
                continue
            
            missing_tenors = set(usd_tenors) - set(tenors)
            if missing_tenors:
                print(f"\n{currency} needs these tickers:")
                # Get pattern from existing ticker
                sample_ticker = df[df['currency_code'] == currency]['bloomberg_ticker'].iloc[0]
                prefix = sample_ticker[:4]  # e.g., "JYSO", "BPSO"
                
                for tenor in sorted(missing_tenors):
                    print(f"  {prefix}{tenor} Curncy")

if __name__ == "__main__":
    verify_tenor_consistency()