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

# Complete GBP OIS curve tickers
gbp_tickers = [
    # Overnight
    {'ticker': 'SONIO/N Index', 'tenor': 'O/N', 'tenor_numeric': 1, 'category': 'RATE'},
    
    # Short end (monthly)
    {'ticker': 'BPSOA Curncy', 'tenor': '1M', 'tenor_numeric': 30, 'category': 'SWAP'},
    {'ticker': 'BPSOB Curncy', 'tenor': '2M', 'tenor_numeric': 60, 'category': 'SWAP'},
    {'ticker': 'BPSOC Curncy', 'tenor': '3M', 'tenor_numeric': 90, 'category': 'SWAP'},
    {'ticker': 'BPSOD Curncy', 'tenor': '4M', 'tenor_numeric': 120, 'category': 'SWAP'},
    {'ticker': 'BPSOE Curncy', 'tenor': '5M', 'tenor_numeric': 150, 'category': 'SWAP'},
    {'ticker': 'BPSOF Curncy', 'tenor': '6M', 'tenor_numeric': 180, 'category': 'SWAP'},
    {'ticker': 'BPSOG Curncy', 'tenor': '7M', 'tenor_numeric': 210, 'category': 'SWAP'},
    {'ticker': 'BPSOH Curncy', 'tenor': '8M', 'tenor_numeric': 240, 'category': 'SWAP'},
    {'ticker': 'BPSOI Curncy', 'tenor': '9M', 'tenor_numeric': 270, 'category': 'SWAP'},
    {'ticker': 'BPSOJ Curncy', 'tenor': '10M', 'tenor_numeric': 300, 'category': 'SWAP'},
    {'ticker': 'BPSOK Curncy', 'tenor': '11M', 'tenor_numeric': 330, 'category': 'SWAP'},
    
    # Long end (yearly)
    {'ticker': 'BPSO1 Curncy', 'tenor': '1Y', 'tenor_numeric': 1, 'category': 'SWAP'},
    {'ticker': 'BPSO2 Curncy', 'tenor': '2Y', 'tenor_numeric': 2, 'category': 'SWAP'},
    {'ticker': 'BPSO3 Curncy', 'tenor': '3Y', 'tenor_numeric': 3, 'category': 'SWAP'},
    {'ticker': 'BPSO4 Curncy', 'tenor': '4Y', 'tenor_numeric': 4, 'category': 'SWAP'},
    {'ticker': 'BPSO5 Curncy', 'tenor': '5Y', 'tenor_numeric': 5, 'category': 'SWAP'},
    {'ticker': 'BPSO6 Curncy', 'tenor': '6Y', 'tenor_numeric': 6, 'category': 'SWAP'},
    {'ticker': 'BPSO7 Curncy', 'tenor': '7Y', 'tenor_numeric': 7, 'category': 'SWAP'},
    {'ticker': 'BPSO8 Curncy', 'tenor': '8Y', 'tenor_numeric': 8, 'category': 'SWAP'},
    {'ticker': 'BPSO9 Curncy', 'tenor': '9Y', 'tenor_numeric': 9, 'category': 'SWAP'},
    {'ticker': 'BPSO10 Curncy', 'tenor': '10Y', 'tenor_numeric': 10, 'category': 'SWAP'},
    {'ticker': 'BPSO12 Curncy', 'tenor': '12Y', 'tenor_numeric': 12, 'category': 'SWAP'},
    {'ticker': 'BPSO15 Curncy', 'tenor': '15Y', 'tenor_numeric': 15, 'category': 'SWAP'},
    {'ticker': 'BPSO20 Curncy', 'tenor': '20Y', 'tenor_numeric': 20, 'category': 'SWAP'},
    {'ticker': 'BPSO25 Curncy', 'tenor': '25Y', 'tenor_numeric': 25, 'category': 'SWAP'},
    {'ticker': 'BPSO30 Curncy', 'tenor': '30Y', 'tenor_numeric': 30, 'category': 'SWAP'},
]

conn = psycopg2.connect(**conn_params)
cursor = conn.cursor()

try:
    # First check if GBP_OIS curve exists in rate_curve_definitions
    cursor.execute("""
        SELECT curve_name FROM rate_curve_definitions 
        WHERE curve_name = 'GBP_OIS'
    """)
    
    if not cursor.fetchone():
        print("Adding GBP_OIS to rate_curve_definitions...")
        cursor.execute("""
            INSERT INTO rate_curve_definitions (
                curve_name,
                currency_code,
                curve_type,
                methodology,
                primary_use
            ) VALUES (%s, %s, %s, %s, %s)
        """, (
            'GBP_OIS',
            'GBP',
            'OIS',
            'Sterling Overnight Index Average (SONIA) based overnight indexed swap curve',
            'Risk-free rate benchmark'
        ))
        print("✓ Added GBP_OIS curve definition")
    
    added_count = 0
    
    print("\nAdding GBP OIS tickers...")
    print("=" * 60)
    
    for ticker_info in gbp_tickers:
        # Check if exists
        cursor.execute("""
            SELECT bloomberg_ticker FROM bloomberg_tickers 
            WHERE bloomberg_ticker = %s
        """, (ticker_info['ticker'],))
        
        if cursor.fetchone():
            print(f"✓ {ticker_info['ticker']} already exists - skipping")
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
                ticker_info['category'],
                ticker_info['tenor'],
                ticker_info['tenor_numeric'],
                'GBP_OIS'
            ))
            
            print(f"✓ Added {ticker_info['ticker']} - {ticker_info['tenor']}")
            added_count += 1
    
    conn.commit()
    
    print(f"\n✓ GBP OIS ticker population complete! Added {added_count} tickers")
    
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