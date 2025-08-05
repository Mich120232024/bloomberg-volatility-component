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

def check_and_add_tenors():
    """Check what's missing and add tenors individually"""
    conn = psycopg2.connect(**conn_params)
    cursor = conn.cursor()
    
    print("CHECKING AND ADDING MISSING TENORS")
    print("=" * 80)
    
    # Key missing tickers to reach 30Y for all currencies
    target_tickers = [
        ('BPSO15 Curncy', 'GBP', 'OIS', '15Y', 5475, 'GBP_OIS', 'GBP OIS 15Y'),
        ('BPSO20 Curncy', 'GBP', 'OIS', '20Y', 7300, 'GBP_OIS', 'GBP OIS 20Y'),
        ('BPSO25 Curncy', 'GBP', 'OIS', '25Y', 9125, 'GBP_OIS', 'GBP OIS 25Y'),
        ('BPSO30 Curncy', 'GBP', 'OIS', '30Y', 9999, 'GBP_OIS', 'GBP OIS 30Y'),
        
        ('SFSO12 Curncy', 'CHF', 'OIS', '12Y', 4380, 'CHF_OIS', 'CHF OIS 12Y'),
        ('SFSO25 Curncy', 'CHF', 'OIS', '25Y', 9125, 'CHF_OIS', 'CHF OIS 25Y'),
        
        ('SKSW12 Curncy', 'SEK', 'IRS', '12Y', 4380, 'SEK_IRS', 'SEK IRS 12Y'),
        ('SKSW25 Curncy', 'SEK', 'IRS', '25Y', 9125, 'SEK_IRS', 'SEK IRS 25Y'),
        
        ('NKSW12 Curncy', 'NOK', 'IRS', '12Y', 4380, 'NOK_IRS', 'NOK IRS 12Y'),
        ('NKSW25 Curncy', 'NOK', 'IRS', '25Y', 9125, 'NOK_IRS', 'NOK IRS 25Y'),
        
        ('NDSO25 Curncy', 'NZD', 'OIS', '25Y', 9125, 'NZD_OIS', 'NZD OIS 25Y'),
        ('NDSO30 Curncy', 'NZD', 'OIS', '30Y', 9999, 'NZD_OIS', 'NZD OIS 30Y'),
    ]
    
    added_count = 0
    
    for ticker, currency, category, tenor, tenor_numeric, curve_name, description in target_tickers:
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
                
                conn.commit()  # Commit each insert individually
                print(f"✓ Added {ticker} - {tenor}")
                added_count += 1
                
            except Exception as e:
                conn.rollback()
                print(f"✗ Failed to add {ticker}: {e}")
    
    print(f"\n✓ Successfully added {added_count} new tenors")
    
    # Final coverage report
    print("\nFINAL COVERAGE REPORT:")
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
    check_and_add_tenors()