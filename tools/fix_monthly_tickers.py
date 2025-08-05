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
    # Remove duplicate/wrong entries - USSOA/B/C are wrong long-term tickers
    cursor.execute("""
        DELETE FROM bloomberg_tickers 
        WHERE curve_name = 'USD_OIS' 
        AND bloomberg_ticker IN ('USSOA Curncy', 'USSOB Curncy', 'USSOC Curncy')
        AND tenor_numeric > 365
    """)
    
    deleted = cursor.rowcount
    print(f"Deleted {deleted} wrong long-term entries")
    
    conn.commit()
    
    # Show remaining tickers
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
    
    print("Remaining USD OIS tickers:")
    for ticker, tenor, tenor_numeric in cursor.fetchall():
        days = tenor_numeric * 365 if tenor_numeric < 100 else tenor_numeric
        print(f"{ticker:15} {tenor:>4} -> {days:>6.0f} days")
        
except Exception as e:
    conn.rollback()
    print(f"Error: {e}")
    raise
finally:
    cursor.close()
    conn.close()