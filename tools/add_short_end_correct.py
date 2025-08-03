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

conn = psycopg2.connect(**conn_params)
cursor = conn.cursor()

try:
    # Get exact schema from existing row
    cursor.execute("""
        SELECT bloomberg_ticker, currency_code, tenor, tenor_numeric, curve_name, is_active
        FROM bloomberg_tickers 
        WHERE bloomberg_ticker = 'USSOD Curncy'
    """)
    
    base_row = cursor.fetchone()
    print(f"Base row: {base_row}")
    
    if base_row:
        # Add 1M, 2M, 3M using minimal required fields
        new_tickers = [
            ('USSOA Curncy', '1M', 30.0),
            ('USSOB Curncy', '2M', 60.0),
            ('USSOC Curncy', '3M', 90.0)
        ]
        
        for ticker, tenor, days in new_tickers:
            # Check if exists
            cursor.execute("SELECT COUNT(*) FROM bloomberg_tickers WHERE bloomberg_ticker = %s", (ticker,))
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO bloomberg_tickers 
                    (bloomberg_ticker, currency_code, tenor, tenor_numeric, curve_name, is_active, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                """, (ticker, base_row[1], tenor, days, base_row[4], base_row[5]))
                print(f"Added {ticker} ({tenor})")
            else:
                print(f"Skipped {ticker} (exists)")
        
        conn.commit()
        print("Done!")
        
        # Show short end
        cursor.execute("""
            SELECT bloomberg_ticker, tenor, tenor_numeric 
            FROM bloomberg_tickers 
            WHERE curve_name = 'USD_OIS' AND tenor_numeric <= 365
            ORDER BY tenor_numeric
        """)
        
        print("\nUSD OIS short end:")
        for row in cursor.fetchall():
            print(f"{row[0]:15} {row[1]:>4} -> {row[2]:>6.0f} days")
    
except Exception as e:
    conn.rollback()
    print(f"Error: {e}")
    raise
finally:
    cursor.close()
    conn.close()