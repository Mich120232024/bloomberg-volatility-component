#!/usr/bin/env python3
import psycopg2
import os

# Direct Azure PostgreSQL connection
conn_params = {
    'host': 'gzcdevserver.postgres.database.azure.com',
    'database': 'gzc_platform',
    'user': 'mikael',
    'port': 5432,
    'password': 'Ii89rra137+*',
    'sslmode': 'require'
}

# Connect to Azure PostgreSQL
conn = psycopg2.connect(**conn_params)
cursor = conn.cursor()

try:
    # Check schema first
    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'rate_curve_definitions'")
    columns = cursor.fetchall()
    print(f"Available columns: {[col[0] for col in columns]}")
    
    # Insert USD OIS curve definition
    cursor.execute("""
        INSERT INTO rate_curve_definitions (curve_name, curve_type, currency_code, methodology, primary_use)
        VALUES ('USD_OIS', 'OIS', 'USD', 'SOFR-based Overnight Index Swap curve', 'FX Options Pricing')
        ON CONFLICT (curve_name) DO UPDATE SET 
            curve_type = EXCLUDED.curve_type,
            currency_code = EXCLUDED.currency_code,
            methodology = EXCLUDED.methodology,
            primary_use = EXCLUDED.primary_use
        RETURNING id
    """)
    curve_id = cursor.fetchone()[0]
    print(f"USD OIS curve ID: {curve_id}")

    # Insert all 21 USD OIS tickers
    tickers = [
        ('USSOA Curncy', 'USD SOFR OIS 1M', '1M', 30),
        ('USSOB Curncy', 'USD SOFR OIS 2M', '2M', 60),
        ('USSOC Curncy', 'USD SOFR OIS 3M', '3M', 90),
        ('USSOD Curncy', 'USD SOFR OIS 4M', '4M', 120),
        ('USSOE Curncy', 'USD SOFR OIS 5M', '5M', 150),
        ('USSOF Curncy', 'USD SOFR OIS 6M', '6M', 180),
        ('USSOG Curncy', 'USD SOFR OIS 7M', '7M', 210),
        ('USSOH Curncy', 'USD SOFR OIS 8M', '8M', 240),
        ('USSOI Curncy', 'USD SOFR OIS 9M', '9M', 270),
        ('USSOJ Curncy', 'USD SOFR OIS 10M', '10M', 300),
        ('USSOK Curncy', 'USD SOFR OIS 11M', '11M', 330),
        ('USSO1 Curncy', 'USD SOFR OIS 1Y', '1Y', 365),
        ('USSO2 Curncy', 'USD SOFR OIS 2Y', '2Y', 730),
        ('USSO3 Curncy', 'USD SOFR OIS 3Y', '3Y', 1095),
        ('USSO4 Curncy', 'USD SOFR OIS 4Y', '4Y', 1460),
        ('USSO5 Curncy', 'USD SOFR OIS 5Y', '5Y', 1825),
        ('USSO6 Curncy', 'USD SOFR OIS 6Y', '6Y', 2190),
        ('USSO7 Curncy', 'USD SOFR OIS 7Y', '7Y', 2555),
        ('USSO8 Curncy', 'USD SOFR OIS 8Y', '8Y', 2920),
        ('USSO9 Curncy', 'USD SOFR OIS 9Y', '9Y', 3285),
        ('USSO10 Curncy', 'USD SOFR OIS 10Y', '10Y', 3650)
    ]

    # Check bloomberg_tickers schema
    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'bloomberg_tickers'")
    ticker_columns = cursor.fetchall()
    print(f"Bloomberg tickers columns: {[col[0] for col in ticker_columns]}")
    
    # Insert tickers
    for ticker, desc, tenor, days in tickers:
        cursor.execute("""
            INSERT INTO bloomberg_tickers (bloomberg_ticker, description, currency_code, category, tenor, instrument_type)
            VALUES (%s, %s, 'USD', 'OIS', %s, 'OIS')
            ON CONFLICT (bloomberg_ticker) DO UPDATE SET description = EXCLUDED.description
            RETURNING id
        """, (ticker, desc, tenor))
        ticker_id = cursor.fetchone()[0]
        
        # Update ticker with curve name  
        cursor.execute("""
            UPDATE bloomberg_tickers 
            SET curve_name = %s, tenor_numeric = %s
            WHERE id = %s
        """, ('USD_OIS', days, ticker_id))
    
    conn.commit()
    print("Successfully inserted USD OIS curve with 21 tickers")
    
    # Verify
    cursor.execute("""
        SELECT COUNT(*) FROM bloomberg_tickers 
        WHERE curve_name = 'USD_OIS'
    """)
    count = cursor.fetchone()[0]
    print(f"Total tickers in USD OIS curve: {count}")
    
except Exception as e:
    conn.rollback()
    print(f"Error: {e}")
    raise
finally:
    cursor.close()
    conn.close()