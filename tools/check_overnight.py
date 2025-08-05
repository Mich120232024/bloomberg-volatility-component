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
    # Check for overnight or very short term tickers
    cursor.execute("""
        SELECT bloomberg_ticker, tenor, tenor_numeric 
        FROM bloomberg_tickers 
        WHERE curve_name = 'USD_OIS' 
        AND (tenor LIKE '%O/N%' OR tenor LIKE '%ON%' OR tenor_numeric < 30)
        ORDER BY tenor_numeric
    """)
    
    print("Checking for overnight tickers:")
    results = cursor.fetchall()
    if results:
        for row in results:
            print(f"  {row[0]:20} tenor={row[1]:>5} tenor_numeric={row[2]}")
    else:
        print("  No overnight tickers found")
        
    # Let's discover what SOFR overnight ticker should be
    print("\nChecking SOFR tickers in database:")
    cursor.execute("""
        SELECT bloomberg_ticker, description, tenor
        FROM bloomberg_tickers 
        WHERE bloomberg_ticker LIKE '%SOFR%' OR description LIKE '%SOFR%'
        LIMIT 10
    """)
    
    for row in cursor.fetchall():
        print(f"  {row[0]:20} {row[1]:40} tenor={row[2]}")
        
finally:
    cursor.close()
    conn.close()