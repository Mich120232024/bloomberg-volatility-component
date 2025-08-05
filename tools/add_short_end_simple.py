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
    # Get a sample row to see the schema
    cursor.execute("""
        SELECT * FROM bloomberg_tickers 
        WHERE curve_name = 'USD_OIS' 
        LIMIT 1
    """)
    
    sample = cursor.fetchone()
    if sample:
        print("Sample row columns count:", len(sample))
        
        # Get column names
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'bloomberg_tickers'
            ORDER BY ordinal_position
        """)
        
        columns = [row[0] for row in cursor.fetchall()]
        print("Columns:", columns[:10])  # First 10 columns
        
        # Simple insert copying from existing USSOD
        cursor.execute("""
            SELECT bloomberg_ticker, currency_code, tenor, tenor_numeric, curve_name,
                   is_active, validation_status, format_type, format_display, data_source
            FROM bloomberg_tickers 
            WHERE bloomberg_ticker = 'USSOD Curncy'
        """)
        
        base_row = cursor.fetchone()
        if base_row:
            print("Base row for copying:", base_row)
            
            # Add 1M, 2M, 3M
            new_tickers = [
                ('USSOA Curncy', '1M', 30.0),
                ('USSOB Curncy', '2M', 60.0),
                ('USSOC Curncy', '3M', 90.0)
            ]
            
            for ticker, tenor, days in new_tickers:
                cursor.execute("""
                    INSERT INTO bloomberg_tickers 
                    (bloomberg_ticker, currency_code, tenor, tenor_numeric, curve_name,
                     is_active, validation_status, format_type, format_display, data_source,
                     created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                """, (ticker, base_row[1], tenor, days, base_row[4],
                      base_row[5], base_row[6], base_row[7], base_row[8], base_row[9]))
                print(f"Added {ticker}")
            
            conn.commit()
            print("Success!")
    
except Exception as e:
    conn.rollback()
    print(f"Error: {e}")
    raise
finally:
    cursor.close()
    conn.close()