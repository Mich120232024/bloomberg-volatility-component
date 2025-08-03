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

# EUR short-term rates to add
eur_short_rates = [
    {'ticker': 'EUDR1W Curncy', 'tenor': '1W', 'tenor_numeric': 7, 'category': 'RATE', 'description': 'EUR Deposit 1W'},
    {'ticker': 'EUDR2W Curncy', 'tenor': '2W', 'tenor_numeric': 14, 'category': 'RATE', 'description': 'EUR Deposit 2W'},
    {'ticker': 'EUR001W Index', 'tenor': '1W', 'tenor_numeric': 7, 'category': 'RATE', 'description': 'EURIBOR 1W'},
]

conn = psycopg2.connect(**conn_params)
cursor = conn.cursor()

try:
    added_count = 0
    
    print("Adding EUR short-term rates...")
    print("=" * 60)
    
    for rate_info in eur_short_rates:
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
                'EUR',
                rate_info['category'],
                rate_info['tenor'],
                rate_info['tenor_numeric'],
                'EUR_OIS',
                rate_info['description']
            ))
            
            print(f"✓ Added {rate_info['ticker']} - {rate_info['tenor']} - {rate_info['description']}")
            added_count += 1
    
    conn.commit()
    
    print(f"\n✓ Added {added_count} EUR short-term rates")
        
except Exception as e:
    conn.rollback()
    print(f"✗ Error: {e}")
finally:
    cursor.close()
    conn.close()