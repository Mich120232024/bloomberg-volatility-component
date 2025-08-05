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

# EUR long-end swap tickers (EUSA = EUR Swap Annual vs 6M EURIBOR)
eur_long_end = [
    {'ticker': 'EUSA1 Curncy', 'tenor': '1Y', 'tenor_numeric': 1},
    {'ticker': 'EUSA2 Curncy', 'tenor': '2Y', 'tenor_numeric': 2},
    {'ticker': 'EUSA3 Curncy', 'tenor': '3Y', 'tenor_numeric': 3},
    {'ticker': 'EUSA4 Curncy', 'tenor': '4Y', 'tenor_numeric': 4},
    {'ticker': 'EUSA5 Curncy', 'tenor': '5Y', 'tenor_numeric': 5},
    {'ticker': 'EUSA6 Curncy', 'tenor': '6Y', 'tenor_numeric': 6},
    {'ticker': 'EUSA7 Curncy', 'tenor': '7Y', 'tenor_numeric': 7},
    {'ticker': 'EUSA8 Curncy', 'tenor': '8Y', 'tenor_numeric': 8},
    {'ticker': 'EUSA9 Curncy', 'tenor': '9Y', 'tenor_numeric': 9},
    {'ticker': 'EUSA10 Curncy', 'tenor': '10Y', 'tenor_numeric': 10},
    {'ticker': 'EUSA12 Curncy', 'tenor': '12Y', 'tenor_numeric': 12},
    {'ticker': 'EUSA15 Curncy', 'tenor': '15Y', 'tenor_numeric': 15},
    {'ticker': 'EUSA20 Curncy', 'tenor': '20Y', 'tenor_numeric': 20},
    {'ticker': 'EUSA25 Curncy', 'tenor': '25Y', 'tenor_numeric': 25},
    {'ticker': 'EUSA30 Curncy', 'tenor': '30Y', 'tenor_numeric': 30},
]

conn = psycopg2.connect(**conn_params)
cursor = conn.cursor()

try:
    added_count = 0
    
    print("Adding EUR long-end swap tickers...")
    print("=" * 60)
    
    for swap_info in eur_long_end:
        # Check if exists
        cursor.execute("""
            SELECT bloomberg_ticker FROM bloomberg_tickers 
            WHERE bloomberg_ticker = %s
        """, (swap_info['ticker'],))
        
        if cursor.fetchone():
            print(f"✓ {swap_info['ticker']} already exists - skipping")
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
                'SWAP',
                swap_info['tenor'],
                swap_info['tenor_numeric'],
                'EUR_OIS'
            ))
            
            print(f"✓ Added {swap_info['ticker']} - {swap_info['tenor']}")
            added_count += 1
    
    conn.commit()
    
    print(f"\n✓ EUR long-end population complete! Added {added_count} tickers")
    
    # Show the complete EUR curve
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
    
    print("\nComplete EUR OIS curve:")
    for row in cursor.fetchall():
        days = row[2] if row[3] == 'RATE' else row[2] * 365
        print(f"  {row[0]:20} {row[1]:>5} -> {days:>6.0f} days")
        
except Exception as e:
    conn.rollback()
    print(f"✗ Error: {e}")
finally:
    cursor.close()
    conn.close()