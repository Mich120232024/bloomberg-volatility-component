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
    # First, delete all wrong USSOA/B/C entries
    cursor.execute("""
        DELETE FROM bloomberg_tickers 
        WHERE curve_name = 'USD_OIS' 
        AND bloomberg_ticker IN ('USSOA Curncy', 'USSOB Curncy', 'USSOC Curncy')
    """)
    deleted = cursor.rowcount
    print(f"Deleted {deleted} wrong USSOA/B/C entries")
    
    # Fix the long-term tickers - store as years (15, 20, 30) in tenor_numeric
    # The gateway will handle the conversion to days
    cursor.execute("""
        UPDATE bloomberg_tickers 
        SET tenor_numeric = 15.0
        WHERE curve_name = 'USD_OIS' AND bloomberg_ticker = 'USSO15 Curncy'
    """)
    
    cursor.execute("""
        UPDATE bloomberg_tickers 
        SET tenor_numeric = 20.0
        WHERE curve_name = 'USD_OIS' AND bloomberg_ticker = 'USSO20 Curncy'
    """)
    
    cursor.execute("""
        UPDATE bloomberg_tickers 
        SET tenor_numeric = 30.0
        WHERE curve_name = 'USD_OIS' AND bloomberg_ticker = 'USSO30 Curncy'
    """)
    
    conn.commit()
    print("Fixed long-term tickers (stored as years)")
    
    # Show final result
    cursor.execute("""
        SELECT bloomberg_ticker, tenor, tenor_numeric 
        FROM bloomberg_tickers 
        WHERE curve_name = 'USD_OIS' 
        ORDER BY 
        CASE 
            -- Monthly tickers
            WHEN bloomberg_ticker LIKE 'USSO_' AND bloomberg_ticker NOT LIKE 'USSO[0-9]%' THEN 
                (CASE 
                    WHEN RIGHT(bloomberg_ticker, 8) = 'D Curncy' THEN ASCII(SUBSTRING(bloomberg_ticker, 5, 1)) - 64
                    WHEN RIGHT(bloomberg_ticker, 8) = 'E Curncy' THEN ASCII(SUBSTRING(bloomberg_ticker, 5, 1)) - 64
                    WHEN RIGHT(bloomberg_ticker, 8) = 'F Curncy' THEN ASCII(SUBSTRING(bloomberg_ticker, 5, 1)) - 64
                    WHEN RIGHT(bloomberg_ticker, 8) = 'G Curncy' THEN ASCII(SUBSTRING(bloomberg_ticker, 5, 1)) - 64
                    WHEN RIGHT(bloomberg_ticker, 8) = 'H Curncy' THEN ASCII(SUBSTRING(bloomberg_ticker, 5, 1)) - 64
                    WHEN RIGHT(bloomberg_ticker, 8) = 'I Curncy' THEN ASCII(SUBSTRING(bloomberg_ticker, 5, 1)) - 64
                    WHEN RIGHT(bloomberg_ticker, 8) = 'J Curncy' THEN ASCII(SUBSTRING(bloomberg_ticker, 5, 1)) - 64
                    WHEN RIGHT(bloomberg_ticker, 8) = 'K Curncy' THEN ASCII(SUBSTRING(bloomberg_ticker, 5, 1)) - 64
                    ELSE 0
                END) * 30
            -- Year tickers  
            WHEN bloomberg_ticker LIKE 'USSO[0-9]%' THEN 
                CAST(SUBSTRING(bloomberg_ticker FROM 'USSO([0-9]+)') AS INTEGER) * 365
            ELSE tenor_numeric * 365
        END
    """)
    
    print("\nFinal USD OIS curve:")
    for ticker, tenor, tenor_numeric in cursor.fetchall():
        # Calculate expected days for display
        if ticker in ['USSO15 Curncy', 'USSO20 Curncy', 'USSO30 Curncy']:
            days = tenor_numeric * 365  # Will be overridden in gateway
            print(f"{ticker:15} {tenor:>4} -> {days:>6.0f} days (converted in gateway)")
        elif tenor_numeric < 100:
            days = tenor_numeric * 365
            print(f"{ticker:15} {tenor:>4} -> {days:>6.0f} days")
        else:
            days = tenor_numeric
            print(f"{ticker:15} {tenor:>4} -> {days:>6.0f} days")
        
except Exception as e:
    conn.rollback()
    print(f"Error: {e}")
    raise
finally:
    cursor.close()
    conn.close()