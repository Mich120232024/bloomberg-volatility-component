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
    # For long-term tickers, we need to store days in tenor_numeric
    # But the field is only 8,4 precision so max is 9999.9999
    # So I'll store years as the smaller value and adjust in the gateway code
    
    # Actually, let me check what the current values are
    cursor.execute("""
        SELECT bloomberg_ticker, tenor, tenor_numeric 
        FROM bloomberg_tickers 
        WHERE curve_name = 'USD_OIS' 
        ORDER BY 
        CASE 
            WHEN tenor_numeric < 100 THEN tenor_numeric * 365
            ELSE tenor_numeric 
        END
    """)
    
    print("Current ticker data:")
    for ticker, tenor, tenor_numeric in cursor.fetchall():
        days = tenor_numeric * 365 if tenor_numeric < 100 else tenor_numeric
        print(f"{ticker:15} {tenor:>4} tenor_numeric: {tenor_numeric:>6.1f} -> days: {days:>6.0f}")
        
except Exception as e:
    print(f"Error: {e}")
    raise
finally:
    cursor.close()
    conn.close()