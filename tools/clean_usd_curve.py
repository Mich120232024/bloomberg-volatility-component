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
    # Delete bad entries
    cursor.execute("""
        DELETE FROM bloomberg_tickers 
        WHERE curve_name = 'USD_OIS' 
        AND bloomberg_ticker IN ('USSOA Curncy', 'USSOB Curncy', 'USSOC Curncy')
    """)
    
    # Keep only clean 1M-11M + 1Y-10Y + 15Y,20Y,30Y
    cursor.execute("""
        UPDATE bloomberg_tickers 
        SET tenor_numeric = 
        CASE 
            WHEN bloomberg_ticker = 'USSO15 Curncy' THEN 5475
            WHEN bloomberg_ticker = 'USSO20 Curncy' THEN 7300  
            WHEN bloomberg_ticker = 'USSO30 Curncy' THEN 10950
            ELSE tenor_numeric
        END
        WHERE curve_name = 'USD_OIS'
    """)
    
    conn.commit()
    print("Cleaned USD curve")
    
except Exception as e:
    conn.rollback()
    print(f"Error: {e}")
finally:
    cursor.close()
    conn.close()