#!/usr/bin/env python3
"""
Load all curve points from ticker_reference table into a dataframe
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from yield_curve_db_endpoint import get_database_connection
import pandas as pd

def load_all_curves():
    """Load all curve data from ticker_reference table"""
    conn = get_database_connection()
    
    # Query ticker_reference directly - the central ticker table
    query = """
        SELECT 
            bloomberg_ticker,
            currency_code,
            instrument_type,
            curve_name,
            is_active
        FROM ticker_reference
        WHERE is_active = true
        ORDER BY currency_code, curve_name, bloomberg_ticker
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    print("=== ALL CURVE MEMBERS FROM TICKER_REFERENCE ===")
    print(f"Total tickers: {len(df)}")
    print(f"Unique currencies: {df['currency_code'].nunique()}")
    print(f"Unique curves: {df['curve_name'].nunique()}")
    
    # Check for duplicates
    duplicates = df[df.duplicated(subset=['bloomberg_ticker'], keep=False)]
    if len(duplicates) > 0:
        print(f"\n⚠️  DUPLICATES FOUND: {len(duplicates)} rows")
        print(duplicates)
    else:
        print("\n✅ No duplicates found")
    
    # Show breakdown by currency/curve
    print("\n=== CURVE BREAKDOWN ===")
    summary = df.groupby(['currency_code', 'curve_name']).agg({
        'bloomberg_ticker': 'count'
    }).rename(columns={'bloomberg_ticker': 'ticker_count'})
    print(summary)
    
    # Show all tickers by currency
    print("\n=== ALL TICKERS BY CURRENCY ===")
    for currency in sorted(df['currency_code'].unique()):
        print(f"\n{currency}:")
        currency_data = df[df['currency_code'] == currency]
        for _, row in currency_data.iterrows():
            print(f"  {row['bloomberg_ticker']} -> {row['curve_name']}")
    
    return df

if __name__ == "__main__":
    df = load_all_curves()