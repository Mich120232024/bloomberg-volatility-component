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

# USD short-term rates to add
usd_short_rates = [
    {'ticker': 'USDR1T Curncy', 'tenor': '1D', 'tenor_numeric': 1, 'category': 'RATE', 'description': 'USD Deposit O/N'},
    {'ticker': 'USDR1W Curncy', 'tenor': '1W', 'tenor_numeric': 7, 'category': 'RATE', 'description': 'USD Deposit 1W'},
    {'ticker': 'USDR2W Curncy', 'tenor': '2W', 'tenor_numeric': 14, 'category': 'RATE', 'description': 'USD Deposit 2W'},
    {'ticker': 'FEDL01 Index', 'tenor': '1D', 'tenor_numeric': 1, 'category': 'RATE', 'description': 'Fed Funds Effective'},
    {'ticker': 'USGG3M Index', 'tenor': '3M', 'tenor_numeric': 90, 'category': 'RATE', 'description': 'US Treasury 3M'},
    {'ticker': 'US0001M Index', 'tenor': '1M', 'tenor_numeric': 30, 'category': 'RATE', 'description': 'USD LIBOR 1M'},
]

conn = psycopg2.connect(**conn_params)
cursor = conn.cursor()

try:
    added_count = 0
    
    print("Adding USD short-term rates...")
    print("=" * 60)
    
    for rate_info in usd_short_rates:
        # Check if exists
        cursor.execute("""
            SELECT bloomberg_ticker FROM bloomberg_tickers 
            WHERE bloomberg_ticker = %s
        """, (rate_info['ticker'],))
        
        if cursor.fetchone():
            print(f"✓ {rate_info['ticker']} already exists - skipping")
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
                rate_info['ticker'],
                'USD',
                rate_info['category'],
                rate_info['tenor'],
                rate_info['tenor_numeric'],
                'USD_OIS',
                rate_info['description']
            ))
            
            print(f"✓ Added {rate_info['ticker']} - {rate_info['tenor']} - {rate_info['description']}")
            added_count += 1
    
    conn.commit()
    
    print(f"\n✓ Added {added_count} USD short-term rates")
    
    # Show updated curve
    cursor.execute("""
        SELECT bloomberg_ticker, tenor, tenor_numeric, category
        FROM bloomberg_tickers
        WHERE curve_name = 'USD_OIS'
        ORDER BY 
            CASE 
                WHEN category = 'RATE' THEN tenor_numeric
                WHEN tenor LIKE '%M' THEN tenor_numeric
                ELSE tenor_numeric * 365
            END
    """)
    
    print("\nUpdated USD OIS curve:")
    for row in cursor.fetchall():
        ticker, tenor, tenor_numeric, category = row
        if category == 'RATE' or 'M' in tenor:
            days = tenor_numeric
        else:
            days = tenor_numeric * 365
        print(f"  {ticker:20} {tenor:>5} -> {days:>6.0f} days")
        
except Exception as e:
    conn.rollback()
    print(f"✗ Error: {e}")
finally:
    cursor.close()
    conn.close()