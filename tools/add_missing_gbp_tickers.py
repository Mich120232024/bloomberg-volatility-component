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

# Missing GBP OIS tickers
missing_tickers = [
    {'ticker': 'BPSO1 Curncy', 'tenor': '1Y', 'tenor_numeric': 1},
    {'ticker': 'BPSO2 Curncy', 'tenor': '2Y', 'tenor_numeric': 2},
    {'ticker': 'BPSO3 Curncy', 'tenor': '3Y', 'tenor_numeric': 3},
    {'ticker': 'BPSO5 Curncy', 'tenor': '5Y', 'tenor_numeric': 5},
    {'ticker': 'BPSO7 Curncy', 'tenor': '7Y', 'tenor_numeric': 7},
    {'ticker': 'BPSO10 Curncy', 'tenor': '10Y', 'tenor_numeric': 10},
    {'ticker': 'BPSO15 Curncy', 'tenor': '15Y', 'tenor_numeric': 15},
    {'ticker': 'BPSO20 Curncy', 'tenor': '20Y', 'tenor_numeric': 20},
    {'ticker': 'BPSO30 Curncy', 'tenor': '30Y', 'tenor_numeric': 30},
]

conn = psycopg2.connect(**conn_params)
cursor = conn.cursor()

try:
    added_count = 0
    
    print("Adding missing GBP OIS tickers...")
    print("=" * 60)
    
    for ticker_info in missing_tickers:
        # Check if exists
        cursor.execute("""
            SELECT bloomberg_ticker FROM bloomberg_tickers 
            WHERE bloomberg_ticker = %s
        """, (ticker_info['ticker'],))
        
        if cursor.fetchone():
            # Update to ensure it's assigned to GBP_OIS
            cursor.execute("""
                UPDATE bloomberg_tickers 
                SET curve_name = 'GBP_OIS'
                WHERE bloomberg_ticker = %s
            """, (ticker_info['ticker'],))
            print(f"✓ Updated {ticker_info['ticker']} to GBP_OIS curve")
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
                'GBP',
                'SWAP',
                ticker_info['tenor'],
                ticker_info['tenor_numeric'],
                'GBP_OIS'
            ))
            
            print(f"✓ Added {ticker_info['ticker']} - {ticker_info['tenor']}")
            added_count += 1
    
    conn.commit()
    
    print(f"\n✓ Added/updated {added_count} tickers")
    
    # Show the complete GBP curve
    cursor.execute("""
        SELECT bloomberg_ticker, tenor, tenor_numeric, category
        FROM bloomberg_tickers
        WHERE curve_name = 'GBP_OIS'
        ORDER BY 
            CASE 
                WHEN category = 'RATE' THEN tenor_numeric  -- Days for rates
                WHEN tenor LIKE '%M' THEN tenor_numeric    -- Days for monthly swaps
                ELSE tenor_numeric * 365                   -- Years to days for yearly swaps
            END
    """)
    
    print("\nComplete GBP OIS curve:")
    count = 0
    for row in cursor.fetchall():
        ticker, tenor, tenor_numeric, category = row
        if category == 'RATE' or 'M' in tenor:
            days = tenor_numeric
        else:
            days = tenor_numeric * 365
        print(f"  {ticker:20} {tenor:>5} -> {days:>6.0f} days")
        count += 1
    
    print(f"\nTotal: {count} tickers for GBP OIS curve")
        
except Exception as e:
    conn.rollback()
    print(f"✗ Error: {e}")
finally:
    cursor.close()
    conn.close()