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
    cursor.execute("""
        SELECT bloomberg_ticker, tenor, tenor_numeric 
        FROM bloomberg_tickers 
        WHERE curve_name = 'USD_OIS' 
        AND bloomberg_ticker IN ('USSOA Curncy', 'USSOB Curncy', 'USSOC Curncy', 'USSO15 Curncy', 'USSO20 Curncy', 'USSO30 Curncy')
        ORDER BY bloomberg_ticker
    """)
    
    print("Problem tickers:")
    for row in cursor.fetchall():
        print(f"{row[0]:15} tenor={row[1]:>4} tenor_numeric={row[2]:>6}")
        
finally:
    cursor.close()
    conn.close()