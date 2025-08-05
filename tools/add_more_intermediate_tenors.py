#!/usr/bin/env python3
import psycopg2

conn_params = {
    'host': 'gzcdevserver.postgres.database.azure.com',
    'database': 'gzc_platform',
    'user': 'mikael',
    'port': 5432,
    'password': 'Ii89rra137+*',
    'sslmode': 'require'
}

# Additional intermediate tenors for USD between 1Y and 2Y
additional_usd_tenors = [
    {'ticker': 'USSO1C Curncy', 'tenor': '15M', 'tenor_numeric': 456, 'description': 'USD OIS 15M'},  # 1.25Y
    {'ticker': 'USSO1F Curncy', 'tenor': '18M', 'tenor_numeric': 548, 'description': 'USD OIS 18M'},  # 1.5Y  
    {'ticker': 'USSO1I Curncy', 'tenor': '21M', 'tenor_numeric': 639, 'description': 'USD OIS 21M'},  # 1.75Y
    {'ticker': 'USSO1Z Curncy', 'tenor': '1.5Y', 'tenor_numeric': 548, 'description': 'USD OIS 1.5Y'},
]

conn = psycopg2.connect(**conn_params)
cursor = conn.cursor()

try:
    print("Adding more intermediate tenors between 1Y and 2Y...")
    print("=" * 60)
    
    added_count = 0
    
    for tenor_info in additional_usd_tenors:
        # Check if exists
        cursor.execute("""
            SELECT bloomberg_ticker FROM bloomberg_tickers 
            WHERE bloomberg_ticker = %s
        """, (tenor_info['ticker'],))
        
        if cursor.fetchone():
            print(f"✓ {tenor_info['ticker']} already exists - skipping")
        else:
            # Insert new ticker
            cursor.execute("""
                INSERT INTO bloomberg_tickers (
                    bloomberg_ticker,
                    currency_code,
                    category,
                    tenor,
                    tenor_numeric,
                    curve_name,
                    description
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                tenor_info['ticker'],
                'USD',
                'OIS',
                tenor_info['tenor'],
                tenor_info['tenor_numeric'],
                'USD_OIS',
                tenor_info['description']
            ))
            
            print(f"✓ Added {tenor_info['ticker']} - {tenor_info['tenor']} - {tenor_info['description']}")
            added_count += 1
    
    conn.commit()
    print(f"\n✓ Added {added_count} additional intermediate tenors")
    
    # Show updated curve between 1-2Y
    cursor.execute("""
        SELECT bloomberg_ticker, tenor, tenor_numeric
        FROM bloomberg_tickers
        WHERE curve_name = 'USD_OIS' 
          AND tenor_numeric >= 365 
          AND tenor_numeric <= 730
        ORDER BY tenor_numeric
    """)
    
    print("\nUSD curve between 1Y and 2Y:")
    for row in cursor.fetchall():
        ticker, tenor, tenor_numeric = row
        days = float(tenor_numeric)
        years = days / 365.0
        print(f"  {ticker:20} {tenor:>6} -> {days:>6.0f} days ({years:.2f}Y)")
        
except Exception as e:
    conn.rollback()
    print(f"✗ Error: {e}")
finally:
    cursor.close()
    conn.close()