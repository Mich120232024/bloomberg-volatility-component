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

def complete_coverage():
    """Complete coverage for all currencies to 30Y with key intermediate tenors"""
    conn = psycopg2.connect(**conn_params)
    cursor = conn.cursor()
    
    print("FINAL COVERAGE COMPLETION")
    print("=" * 80)
    
    # Final missing tickers for complete coverage
    final_tickers = [
        # GBP extend to 30Y (currently stops at 9Y)
        ('BPSO12 Curncy', 'GBP', 'OIS', '12Y', 4380, 'GBP_OIS', 'GBP OIS 12Y'),
        ('BPSO25 Curncy', 'GBP', 'OIS', '25Y', 9125, 'GBP_OIS', 'GBP OIS 25Y'),
        ('BPSO30 Curncy', 'GBP', 'OIS', '30Y', 9999, 'GBP_OIS', 'GBP OIS 30Y'),
        
        # CHF extend to 30Y  
        ('SFSO30 Curncy', 'CHF', 'OIS', '30Y', 9999, 'CHF_OIS', 'CHF OIS 30Y'),
        
        # SEK extend to 30Y
        ('SKSW30 Curncy', 'SEK', 'IRS', '30Y', 9999, 'SEK_IRS', 'SEK IRS 30Y'),
        
        # NOK extend to 30Y
        ('NKSW30 Curncy', 'NOK', 'IRS', '30Y', 9999, 'NOK_IRS', 'NOK IRS 30Y'),
        
        # Add key intermediate tenors missing across currencies
        ('EUSA8 Curncy', 'EUR', 'OIS', '8Y', 2920, 'EUR_OIS', 'EUR OIS 8Y'),
        ('EUSA9 Curncy', 'EUR', 'OIS', '9Y', 3285, 'EUR_OIS', 'EUR OIS 9Y'),
        ('EUSA12 Curncy', 'EUR', 'OIS', '12Y', 4380, 'EUR_OIS', 'EUR OIS 12Y'),
        
        ('JYSO8 Curncy', 'JPY', 'OIS', '8Y', 2920, 'JPY_OIS', 'JPY OIS 8Y'),
        ('JYSO9 Curncy', 'JPY', 'OIS', '9Y', 3285, 'JPY_OIS', 'JPY OIS 9Y'),
        ('JYSO12 Curncy', 'JPY', 'OIS', '12Y', 4380, 'JPY_OIS', 'JPY OIS 12Y'),
        
        ('BPSO8 Curncy', 'GBP', 'OIS', '8Y', 2920, 'GBP_OIS', 'GBP OIS 8Y'),
        ('BPSO9 Curncy', 'GBP', 'OIS', '9Y', 3285, 'GBP_OIS', 'GBP OIS 9Y'),
        
        ('SFSO8 Curncy', 'CHF', 'OIS', '8Y', 2920, 'CHF_OIS', 'CHF OIS 8Y'),
        ('SFSO9 Curncy', 'CHF', 'OIS', '9Y', 3285, 'CHF_OIS', 'CHF OIS 9Y'),
        
        ('CDSO8 Curncy', 'CAD', 'OIS', '8Y', 2920, 'CAD_OIS', 'CAD OIS 8Y'),
        ('CDSO9 Curncy', 'CAD', 'OIS', '9Y', 3285, 'CAD_OIS', 'CAD OIS 9Y'),
        ('CDSO12 Curncy', 'CAD', 'OIS', '12Y', 4380, 'CAD_OIS', 'CAD OIS 12Y'),
        
        ('ADSO8 Curncy', 'AUD', 'OIS', '8Y', 2920, 'AUD_OIS', 'AUD OIS 8Y'),
        ('ADSO9 Curncy', 'AUD', 'OIS', '9Y', 3285, 'AUD_OIS', 'AUD OIS 9Y'),
        ('ADSO12 Curncy', 'AUD', 'OIS', '12Y', 4380, 'AUD_OIS', 'AUD OIS 12Y'),
        
        ('NDSO8 Curncy', 'NZD', 'OIS', '8Y', 2920, 'NZD_OIS', 'NZD OIS 8Y'),
        ('NDSO9 Curncy', 'NZD', 'OIS', '9Y', 3285, 'NZD_OIS', 'NZD OIS 9Y'),
        ('NDSO12 Curncy', 'NZD', 'OIS', '12Y', 4380, 'NZD_OIS', 'NZD OIS 12Y'),
        
        ('SKSW8 Curncy', 'SEK', 'IRS', '8Y', 2920, 'SEK_IRS', 'SEK IRS 8Y'),
        ('SKSW9 Curncy', 'SEK', 'IRS', '9Y', 3285, 'SEK_IRS', 'SEK IRS 9Y'),
        
        ('NKSW8 Curncy', 'NOK', 'IRS', '8Y', 2920, 'NOK_IRS', 'NOK IRS 8Y'),
        ('NKSW9 Curncy', 'NOK', 'IRS', '9Y', 3285, 'NOK_IRS', 'NOK IRS 9Y'),
    ]
    
    added_count = 0
    
    for ticker, currency, category, tenor, tenor_numeric, curve_name, description in final_tickers:
        # Check if ticker exists
        cursor.execute("SELECT bloomberg_ticker FROM bloomberg_tickers WHERE bloomberg_ticker = %s", (ticker,))
        
        if cursor.fetchone():
            print(f"✓ {ticker} already exists")
        else:
            # Add the ticker
            try:
                cursor.execute("""
                    INSERT INTO bloomberg_tickers (
                        bloomberg_ticker, currency_code, category, tenor, 
                        tenor_numeric, curve_name, description
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (ticker, currency, category, tenor, tenor_numeric, curve_name, description))
                
                conn.commit()
                print(f"✓ Added {ticker} - {tenor}")
                added_count += 1
                
            except Exception as e:
                conn.rollback()
                print(f"✗ Failed to add {ticker}: {e}")
    
    print(f"\n✓ Successfully added {added_count} final tenors")
    
    # Final comprehensive coverage report
    print("\n" + "=" * 80)
    print("COMPREHENSIVE G10 COVERAGE FINAL REPORT")
    print("=" * 80)
    
    currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD', 'SEK', 'NOK']
    
    for currency in currencies:
        cursor.execute("""
            SELECT COUNT(*) as count, MIN(tenor_numeric) as min_days, MAX(tenor_numeric) as max_days
            FROM bloomberg_tickers 
            WHERE currency_code = %s AND curve_name IS NOT NULL
            ORDER BY tenor_numeric
        """, (currency,))
        
        result = cursor.fetchone()
        count, min_days, max_days = result
        min_years = float(min_days) / 365.0
        max_years = float(max_days) / 365.0
        
        # Get curve name
        cursor.execute("""
            SELECT DISTINCT curve_name FROM bloomberg_tickers 
            WHERE currency_code = %s AND curve_name IS NOT NULL
        """, (currency,))
        curve_name = cursor.fetchone()[0]
        
        print(f'{currency} ({curve_name}): {count:>2} tickers, {min_years:.3f}Y to {max_years:.1f}Y')
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    complete_coverage()