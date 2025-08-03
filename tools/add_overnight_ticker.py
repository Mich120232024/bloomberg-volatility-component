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

conn = psycopg2.connect(**conn_params)
cursor = conn.cursor()

try:
    # First check if it already exists
    cursor.execute("""
        SELECT bloomberg_ticker FROM bloomberg_tickers 
        WHERE bloomberg_ticker = 'SOFRRATE Index'
    """)
    
    if cursor.fetchone():
        print("✓ SOFRRATE Index already exists in database")
    else:
        # Get a reference ticker to copy structure from
        cursor.execute("""
            SELECT * FROM bloomberg_tickers 
            WHERE bloomberg_ticker = 'USSOD Curncy'
            LIMIT 1
        """)
        
        reference = cursor.fetchone()
        if reference:
            # Insert the overnight ticker - use minimal columns
            cursor.execute("""
                INSERT INTO bloomberg_tickers (
                    bloomberg_ticker,
                    currency_code,
                    category,
                    tenor,
                    tenor_numeric,
                    curve_name
                ) VALUES (
                    'SOFRRATE Index',
                    'USD',
                    'RATE',
                    'O/N',
                    1.0,  -- 1 day
                    'USD_OIS'
                )
            """)
            
            conn.commit()
            print("✓ Added SOFRRATE Index to database")
            print("  tenor: O/N")
            print("  tenor_numeric: 1 day")
            print("  description: United States SOFR Secured Overnight Rate")
        else:
            print("✗ Could not find reference ticker")
    
    # Verify all short-term tickers
    cursor.execute("""
        SELECT bloomberg_ticker, tenor, tenor_numeric
        FROM bloomberg_tickers
        WHERE curve_name = 'USD_OIS' AND tenor_numeric <= 90
        ORDER BY tenor_numeric
    """)
    
    print("\nUSD OIS short-end tickers:")
    for row in cursor.fetchall():
        print(f"  {row[0]:20} {row[1]:>5} -> {row[2]:>4.0f} days")
        
except Exception as e:
    conn.rollback()
    print(f"✗ Error: {e}")
finally:
    cursor.close()
    conn.close()