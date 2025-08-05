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
    # Add missing 1M, 2M, 3M tickers with proper complete schema
    short_tickers = [
        ('USSOA Curncy', '1M', 30.0, 'USD'),
        ('USSOB Curncy', '2M', 60.0, 'USD'), 
        ('USSOC Curncy', '3M', 90.0, 'USD')
    ]
    
    for ticker_symbol, tenor_label, days, currency in short_tickers:
        # Check if exists first
        cursor.execute("""
            SELECT COUNT(*) FROM bloomberg_tickers 
            WHERE bloomberg_ticker = %s
        """, (ticker_symbol,))
        
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.execute("""
                INSERT INTO bloomberg_tickers 
                (bloomberg_ticker, currency_code, tenor, tenor_numeric, curve_name, 
                 created_at, updated_at, is_active, validation_status, format_type, format_display, 
                 data_source, instrument_type, market_sector, quote_type)
                VALUES (%s, %s, %s, %s, 'USD_OIS',
                        NOW(), NOW(), true, 'untested', 'decimal_percentage', '%',
                        'manual', 'swap', 'rates', 'mid')
            """, (ticker_symbol, currency, tenor_label, days))
            print(f"Added {ticker_symbol} ({tenor_label}) - {days} days")
        else:
            print(f"Skipped {ticker_symbol} (already exists)")
    
    conn.commit()
    print("Successfully added 1M, 2M, 3M tickers")
    
    # Show complete short end now
    cursor.execute("""
        SELECT bloomberg_ticker, tenor, tenor_numeric 
        FROM bloomberg_tickers 
        WHERE curve_name = 'USD_OIS' AND tenor_numeric <= 365
        ORDER BY tenor_numeric
    """)
    
    print("\nComplete USD OIS short end:")
    for ticker, tenor, tenor_numeric in cursor.fetchall():
        print(f"{ticker:15} {tenor:>4} -> {tenor_numeric:>6.0f} days")
    
except Exception as e:
    conn.rollback()
    print(f"Error: {e}")
    raise
finally:
    cursor.close()
    conn.close()