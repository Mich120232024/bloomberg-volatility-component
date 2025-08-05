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
    # Add missing 1M, 2M, 3M tickers with proper schema
    monthly_tickers = [
        ('USSOA Curncy', '1M', 30.0),
        ('USSOB Curncy', '2M', 60.0), 
        ('USSOC Curncy', '3M', 90.0)
    ]
    
    for ticker, tenor, tenor_numeric in monthly_tickers:
        # Check if exists first
        cursor.execute("""
            SELECT COUNT(*) FROM bloomberg_tickers 
            WHERE curve_name = 'USD_OIS' AND bloomberg_ticker = %s
        """, (ticker,))
        
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO bloomberg_tickers 
                (bloomberg_ticker, currency_code, tenor, tenor_numeric, curve_name, created_at, updated_at, 
                 is_active, validation_status, format_type, format_display, data_source)
                VALUES (%s, 'USD', %s, %s, 'USD_OIS', NOW(), NOW(), 
                        true, 'untested', 'decimal_percentage', '%', 'manual')
            """, (ticker, tenor, tenor_numeric))
            print(f"Added {ticker} ({tenor})")
        else:
            print(f"Skipped {ticker} (already exists)")
    
    conn.commit()
    print("Completed adding missing monthly tickers")
    
except Exception as e:
    conn.rollback()
    print(f"Error: {e}")
    raise
finally:
    cursor.close()
    conn.close()