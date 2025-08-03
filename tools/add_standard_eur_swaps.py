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

# Standard EUR swap tickers based on market conventions
# EUSWEA = EUR Swap vs 6M EURIBOR, Annual/Annual basis
# EUSWEC = EUR Swap vs 3M EURIBOR, Quarterly/Quarterly basis
# ESTR-based swaps are the new standard for EUR OIS

eur_swaps = [
    # Short-term EURIBOR rates (already validated as working)
    {'ticker': 'EUR001W Index', 'tenor': '1W', 'tenor_numeric': 7, 'category': 'RATE'},
    {'ticker': 'EUR002W Index', 'tenor': '2W', 'tenor_numeric': 14, 'category': 'RATE'},
    {'ticker': 'EUR001M Index', 'tenor': '1M', 'tenor_numeric': 30, 'category': 'RATE'},
    {'ticker': 'EUR002M Index', 'tenor': '2M', 'tenor_numeric': 60, 'category': 'RATE'},
    {'ticker': 'EUR003M Index', 'tenor': '3M', 'tenor_numeric': 90, 'category': 'RATE'},
    {'ticker': 'EUR006M Index', 'tenor': '6M', 'tenor_numeric': 180, 'category': 'RATE'},
    {'ticker': 'EUR009M Index', 'tenor': '9M', 'tenor_numeric': 270, 'category': 'RATE'},
    {'ticker': 'EUR012M Index', 'tenor': '12M', 'tenor_numeric': 365, 'category': 'RATE'},
    
    # Standard EUR swap rates vs 6M EURIBOR (Annual/Annual)
    {'ticker': 'EUSWEA1 Curncy', 'tenor': '1Y', 'tenor_numeric': 1, 'category': 'SWAP'},
    {'ticker': 'EUSWEA2 Curncy', 'tenor': '2Y', 'tenor_numeric': 2, 'category': 'SWAP'},
    {'ticker': 'EUSWEA3 Curncy', 'tenor': '3Y', 'tenor_numeric': 3, 'category': 'SWAP'},
    {'ticker': 'EUSWEA4 Curncy', 'tenor': '4Y', 'tenor_numeric': 4, 'category': 'SWAP'},
    {'ticker': 'EUSWEA5 Curncy', 'tenor': '5Y', 'tenor_numeric': 5, 'category': 'SWAP'},
    {'ticker': 'EUSWEA6 Curncy', 'tenor': '6Y', 'tenor_numeric': 6, 'category': 'SWAP'},
    {'ticker': 'EUSWEA7 Curncy', 'tenor': '7Y', 'tenor_numeric': 7, 'category': 'SWAP'},
    {'ticker': 'EUSWEA8 Curncy', 'tenor': '8Y', 'tenor_numeric': 8, 'category': 'SWAP'},
    {'ticker': 'EUSWEA9 Curncy', 'tenor': '9Y', 'tenor_numeric': 9, 'category': 'SWAP'},
    {'ticker': 'EUSWEA10 Curncy', 'tenor': '10Y', 'tenor_numeric': 10, 'category': 'SWAP'},
    {'ticker': 'EUSWEA12 Curncy', 'tenor': '12Y', 'tenor_numeric': 12, 'category': 'SWAP'},
    {'ticker': 'EUSWEA15 Curncy', 'tenor': '15Y', 'tenor_numeric': 15, 'category': 'SWAP'},
    {'ticker': 'EUSWEA20 Curncy', 'tenor': '20Y', 'tenor_numeric': 20, 'category': 'SWAP'},
    {'ticker': 'EUSWEA25 Curncy', 'tenor': '25Y', 'tenor_numeric': 25, 'category': 'SWAP'},
    {'ticker': 'EUSWEA30 Curncy', 'tenor': '30Y', 'tenor_numeric': 30, 'category': 'SWAP'},
]

conn = psycopg2.connect(**conn_params)
cursor = conn.cursor()

try:
    added_count = 0
    skipped_count = 0
    
    print("Adding standard EUR swap tickers...")
    print("=" * 60)
    
    for swap_info in eur_swaps:
        # Check if exists
        cursor.execute("""
            SELECT bloomberg_ticker FROM bloomberg_tickers 
            WHERE bloomberg_ticker = %s
        """, (swap_info['ticker'],))
        
        if cursor.fetchone():
            print(f"✓ {swap_info['ticker']} already exists - skipping")
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
                swap_info['ticker'],
                'EUR',
                swap_info['category'],
                swap_info['tenor'],
                swap_info['tenor_numeric'],
                'EUR_OIS'
            ))
            
            print(f"✓ Added {swap_info['ticker']} - {swap_info['tenor']}")
            added_count += 1
    
    conn.commit()
    
    print(f"\n✓ EUR swap curve population complete!")
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
        print(f"  {row[0]:25} {row[1]:>5} -> {days:>6.0f} days")
        
except Exception as e:
    conn.rollback()
    print(f"✗ Error: {e}")
finally:
    cursor.close()
    conn.close()

print("\nNote: These tickers need to be validated with Bloomberg Terminal")
print("If any don't return data, they should be replaced with the correct tickers")