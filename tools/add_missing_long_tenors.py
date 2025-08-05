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

def add_missing_long_tenors():
    """Add missing long-end tenors to bring all currencies to 30Y coverage"""
    conn = psycopg2.connect(**conn_params)
    cursor = conn.cursor()
    
    print("ADDING MISSING LONG-END TENORS")
    print("=" * 80)
    
    # Focus on adding long-end coverage that's missing
    missing_tenors = [
        # GBP - extend to 30Y
        ('BPSO12 Curncy', 'GBP', 'OIS', '12Y', 4380, 'GBP_OIS', 'GBP OIS 12Y'),
        ('BPSO15 Curncy', 'GBP', 'OIS', '15Y', 5475, 'GBP_OIS', 'GBP OIS 15Y'),
        ('BPSO20 Curncy', 'GBP', 'OIS', '20Y', 7300, 'GBP_OIS', 'GBP OIS 20Y'),
        ('BPSO25 Curncy', 'GBP', 'OIS', '25Y', 9125, 'GBP_OIS', 'GBP OIS 25Y'),
        ('BPSO30 Curncy', 'GBP', 'OIS', '30Y', 9999, 'GBP_OIS', 'GBP OIS 30Y'),
        
        # CHF - extend to 30Y
        ('SFSO8 Curncy', 'CHF', 'OIS', '8Y', 2920, 'CHF_OIS', 'CHF OIS 8Y'),
        ('SFSO9 Curncy', 'CHF', 'OIS', '9Y', 3285, 'CHF_OIS', 'CHF OIS 9Y'),
        ('SFSO10 Curncy', 'CHF', 'OIS', '10Y', 3650, 'CHF_OIS', 'CHF OIS 10Y'),
        ('SFSO12 Curncy', 'CHF', 'OIS', '12Y', 4380, 'CHF_OIS', 'CHF OIS 12Y'),
        ('SFSO25 Curncy', 'CHF', 'OIS', '25Y', 9125, 'CHF_OIS', 'CHF OIS 25Y'),
        
        # SEK - extend to 30Y
        ('SKSW8 Curncy', 'SEK', 'IRS', '8Y', 2920, 'SEK_IRS', 'SEK IRS 8Y'),
        ('SKSW9 Curncy', 'SEK', 'IRS', '9Y', 3285, 'SEK_IRS', 'SEK IRS 9Y'),
        ('SKSW12 Curncy', 'SEK', 'IRS', '12Y', 4380, 'SEK_IRS', 'SEK IRS 12Y'),
        ('SKSW25 Curncy', 'SEK', 'IRS', '25Y', 9125, 'SEK_IRS', 'SEK IRS 25Y'),
        
        # NOK - extend to 30Y  
        ('NKSW8 Curncy', 'NOK', 'IRS', '8Y', 2920, 'NOK_IRS', 'NOK IRS 8Y'),
        ('NKSW9 Curncy', 'NOK', 'IRS', '9Y', 3285, 'NOK_IRS', 'NOK IRS 9Y'),
        ('NKSW12 Curncy', 'NOK', 'IRS', '12Y', 4380, 'NOK_IRS', 'NOK IRS 12Y'),
        ('NKSW25 Curncy', 'NOK', 'IRS', '25Y', 9125, 'NOK_IRS', 'NOK IRS 25Y'),
        ('NKSW30 Curncy', 'NOK', 'IRS', '30Y', 9999, 'NOK_IRS', 'NOK IRS 30Y'),
        
        # NZD - extend to 30Y
        ('NDSO12 Curncy', 'NZD', 'OIS', '12Y', 4380, 'NZD_OIS', 'NZD OIS 12Y'),
        ('NDSO15 Curncy', 'NZD', 'OIS', '15Y', 5475, 'NZD_OIS', 'NZD OIS 15Y'),
        ('NDSO25 Curncy', 'NZD', 'OIS', '25Y', 9125, 'NZD_OIS', 'NZD OIS 25Y'),
        ('NDSO30 Curncy', 'NZD', 'OIS', '30Y', 9999, 'NZD_OIS', 'NZD OIS 30Y'),
        
        # Add intermediate tenors for better coverage
        ('EUSA8 Curncy', 'EUR', 'OIS', '8Y', 2920, 'EUR_OIS', 'EUR OIS 8Y'),
        ('EUSA9 Curncy', 'EUR', 'OIS', '9Y', 3285, 'EUR_OIS', 'EUR OIS 9Y'),
        ('EUSA12 Curncy', 'EUR', 'OIS', '12Y', 4380, 'EUR_OIS', 'EUR OIS 12Y'),
        
        ('JYSO8 Curncy', 'JPY', 'OIS', '8Y', 2920, 'JPY_OIS', 'JPY OIS 8Y'),
        ('JYSO9 Curncy', 'JPY', 'OIS', '9Y', 3285, 'JPY_OIS', 'JPY OIS 9Y'),
        ('JYSO12 Curncy', 'JPY', 'OIS', '12Y', 4380, 'JPY_OIS', 'JPY OIS 12Y'),
    ]
    
    added_count = 0
    
    for ticker, currency, category, tenor, tenor_numeric, curve_name, description in missing_tenors:
        try:
            cursor.execute("""
                INSERT INTO bloomberg_tickers (
                    bloomberg_ticker, currency_code, category, tenor, 
                    tenor_numeric, curve_name, description
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (ticker, currency, category, tenor, tenor_numeric, curve_name, description))
            
            print(f"✓ Added {ticker} - {tenor}")
            added_count += 1
            
        except Exception as e:
            if "duplicate key" in str(e).lower():
                print(f"✗ {ticker} already exists")
            else:
                print(f"✗ {ticker} error: {e}")
    
    conn.commit()
    print(f"\n✓ Added {added_count} long-end tenors")
    
    # Final coverage report
    print("\nUPDATED COVERAGE:")
    currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD', 'SEK', 'NOK']
    
    for currency in currencies:
        cursor.execute("""
            SELECT COUNT(*) as count, MIN(tenor_numeric) as min_days, MAX(tenor_numeric) as max_days
            FROM bloomberg_tickers 
            WHERE currency_code = %s AND curve_name IS NOT NULL
        """, (currency,))
        
        result = cursor.fetchone()
        count, min_days, max_days = result
        min_years = float(min_days) / 365.0
        max_years = float(max_days) / 365.0
        print(f'{currency}: {count:>2} tickers, {min_years:.3f}Y to {max_years:.1f}Y')
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    add_missing_long_tenors()