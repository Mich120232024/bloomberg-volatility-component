#!/usr/bin/env python3
import psycopg2

# Direct Azure PostgreSQL connection
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
    # Fix the long-term tickers with correct tenor_numeric (in years)
    corrections = [
        ('USSO15 Curncy', '15Y', 15),   # 15 years
        ('USSO20 Curncy', '20Y', 20),   # 20 years  
        ('USSO30 Curncy', '30Y', 30),   # 30 years
    ]
    
    for ticker, tenor, days in corrections:
        cursor.execute("""
            UPDATE bloomberg_tickers 
            SET tenor = %s, tenor_numeric = %s
            WHERE bloomberg_ticker = %s AND curve_name = 'USD_OIS'
        """, (tenor, days, ticker))
        print(f"Updated {ticker}: {tenor} ({days} years)")
    
    conn.commit()
    
    # Verify the corrections
    cursor.execute("""
        SELECT bloomberg_ticker, tenor, tenor_numeric 
        FROM bloomberg_tickers 
        WHERE curve_name = 'USD_OIS' AND bloomberg_ticker IN ('USSO15 Curncy', 'USSO20 Curncy', 'USSO30 Curncy')
        ORDER BY tenor_numeric
    """)
    
    print("\nCorrected long-term tickers:")
    for ticker, tenor, years in cursor.fetchall():
        print(f"{ticker:15} {tenor:>4} ({years:>5.0f} years)")
        
except Exception as e:
    conn.rollback()
    print(f"Error: {e}")
    raise
finally:
    cursor.close()
    conn.close()