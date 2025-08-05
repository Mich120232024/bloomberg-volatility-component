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
    # Check for EUR-related tickers
    print("Checking for EUR tickers in database:")
    cursor.execute("""
        SELECT bloomberg_ticker, description, tenor, category
        FROM bloomberg_tickers 
        WHERE currency_code = 'EUR' 
        AND (category = 'OIS' OR category = 'RATE' OR category = 'SWAP')
        ORDER BY tenor_numeric
        LIMIT 20
    """)
    
    for row in cursor.fetchall():
        print(f"  {row[0]:20} {row[1]:40} tenor={row[2]:>5} cat={row[3]}")
    
    # Check for ESTR
    print("\nChecking for ESTR tickers:")
    cursor.execute("""
        SELECT bloomberg_ticker, description, currency_code
        FROM bloomberg_tickers 
        WHERE bloomberg_ticker LIKE '%ESTR%' OR description LIKE '%ESTR%'
        LIMIT 10
    """)
    
    for row in cursor.fetchall():
        print(f"  {row[0]:20} {row[1]:40} ccy={row[2]}")
        
    # Check for EESWE pattern
    print("\nChecking for EESWE pattern (EUR OIS):")
    cursor.execute("""
        SELECT bloomberg_ticker, description, tenor
        FROM bloomberg_tickers 
        WHERE bloomberg_ticker LIKE 'EESWE%'
        ORDER BY bloomberg_ticker
        LIMIT 20
    """)
    
    for row in cursor.fetchall():
        print(f"  {row[0]:20} {row[1]:40} tenor={row[2]}")
        
finally:
    cursor.close()
    conn.close()