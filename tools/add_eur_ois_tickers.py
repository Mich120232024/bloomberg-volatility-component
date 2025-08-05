#!/usr/bin/env python3
import psycopg2
from datetime import datetime

conn_params = {
    'host': 'gzcdevserver.postgres.database.azure.com',
    'database': 'gzc_platform',
    'user': 'mikael',
    'port': 5432,
    'password': 'Ii89rra137+*',
    'sslmode': 'require'
}

# EUR OIS tickers discovered and validated
eur_tickers = [
    # Overnight
    {'ticker': 'ESTR Index', 'tenor': 'O/N', 'tenor_numeric': 1, 'category': 'RATE'},
    
    # Short-term (Euribor)
    {'ticker': 'EUR001M Index', 'tenor': '1M', 'tenor_numeric': 30, 'category': 'RATE'},
    {'ticker': 'EUR002M Index', 'tenor': '2M', 'tenor_numeric': 60, 'category': 'RATE'},
    {'ticker': 'EUR003M Index', 'tenor': '3M', 'tenor_numeric': 90, 'category': 'RATE'},
    {'ticker': 'EUR006M Index', 'tenor': '6M', 'tenor_numeric': 180, 'category': 'RATE'},
    {'ticker': 'EUR009M Index', 'tenor': '9M', 'tenor_numeric': 270, 'category': 'RATE'},
    {'ticker': 'EUR012M Index', 'tenor': '12M', 'tenor_numeric': 365, 'category': 'RATE'},
    
    # OIS swaps (yearly)
    {'ticker': 'EESWE1 Curncy', 'tenor': '1Y', 'tenor_numeric': 1, 'category': 'SWAP'},
    {'ticker': 'EESWE2 Curncy', 'tenor': '2Y', 'tenor_numeric': 2, 'category': 'SWAP'},
    {'ticker': 'EESWE3 Curncy', 'tenor': '3Y', 'tenor_numeric': 3, 'category': 'SWAP'},
    {'ticker': 'EESWE5 Curncy', 'tenor': '5Y', 'tenor_numeric': 5, 'category': 'SWAP'},
    {'ticker': 'EESWE7 Curncy', 'tenor': '7Y', 'tenor_numeric': 7, 'category': 'SWAP'},
    {'ticker': 'EESWE10 Curncy', 'tenor': '10Y', 'tenor_numeric': 10, 'category': 'SWAP'},
    {'ticker': 'EESWE15 Curncy', 'tenor': '15Y', 'tenor_numeric': 15, 'category': 'SWAP'},
    {'ticker': 'EESWE20 Curncy', 'tenor': '20Y', 'tenor_numeric': 20, 'category': 'SWAP'},
    {'ticker': 'EESWE30 Curncy', 'tenor': '30Y', 'tenor_numeric': 30, 'category': 'SWAP'},
]

conn = psycopg2.connect(**conn_params)
cursor = conn.cursor()

try:
    added_count = 0
    skipped_count = 0
    
    for ticker_info in eur_tickers:
        # Check if exists
        cursor.execute("""
            SELECT bloomberg_ticker FROM bloomberg_tickers 
            WHERE bloomberg_ticker = %s
        """, (ticker_info['ticker'],))
        
        if cursor.fetchone():
            print(f"✓ {ticker_info['ticker']} already exists - skipping")
            skipped_count += 1
        else:
            # Insert new ticker
            cursor.execute("""
                INSERT INTO bloomberg_tickers (
                    bloomberg_ticker,
                    currency_code,
                    category,
                    tenor,
                    tenor_numeric,
                    curve_name
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                ticker_info['ticker'],
                'EUR',
                ticker_info['category'],
                ticker_info['tenor'],
                ticker_info['tenor_numeric'],
                'EUR_OIS'
            ))
            
            print(f"✓ Added {ticker_info['ticker']} - {ticker_info['tenor']}")
            added_count += 1
    
    conn.commit()
    
    print(f"\n✓ EUR OIS curve population complete!")
    print(f"  Added: {added_count} tickers")
    print(f"  Skipped: {skipped_count} existing")
    
    # Verify the curve
    cursor.execute("""
        SELECT bloomberg_ticker, tenor, tenor_numeric, category
        FROM bloomberg_tickers
        WHERE curve_name = 'EUR_OIS'
        ORDER BY 
            CASE 
                WHEN category = 'RATE' THEN tenor_numeric  -- Days for rates
                ELSE tenor_numeric * 365  -- Years to days for swaps
            END
    """)
    
    print("\nEUR OIS curve tickers:")
    for row in cursor.fetchall():
        days = row[2] if row[3] == 'RATE' else row[2] * 365
        print(f"  {row[0]:20} {row[1]:>5} -> {days:>5.0f} days")
        
except Exception as e:
    conn.rollback()
    print(f"✗ Error: {e}")
finally:
    cursor.close()
    conn.close()