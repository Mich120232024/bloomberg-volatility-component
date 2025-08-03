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

def add_missing_standard_tenors():
    """Add missing standard tenors for all currencies"""
    conn = psycopg2.connect(**conn_params)
    cursor = conn.cursor()
    
    print("ADDING MISSING STANDARD TENORS")
    print("=" * 60)
    
    # Missing tenors to add for each currency
    missing_tenors = [
        # EUR missing: 2W, 2M, 9M, 1Y
        ('EUR001W Index', 'EUR', 'RATE', '1W', 7, 'EUR_OIS', 'EUR 1W Rate'),
        ('EUR002W Index', 'EUR', 'RATE', '2W', 14, 'EUR_OIS', 'EUR 2W Rate'),
        ('EUR002M Index', 'EUR', 'RATE', '2M', 60, 'EUR_OIS', 'EUR 2M Rate'),
        ('EUR009M Index', 'EUR', 'RATE', '9M', 270, 'EUR_OIS', 'EUR 9M Rate'),
        ('EUSA1 Curncy', 'EUR', 'OIS', '1Y', 365, 'EUR_OIS', 'EUR OIS 1Y'),
        
        # GBP missing: 1W, 2W, 1Y, 2Y, 3Y, 5Y, 7Y, 10Y, 15Y, 20Y, 30Y
        ('GBP001W Index', 'GBP', 'RATE', '1W', 7, 'GBP_OIS', 'GBP 1W Rate'),
        ('GBP002W Index', 'GBP', 'RATE', '2W', 14, 'GBP_OIS', 'GBP 2W Rate'),
        ('BPSO1 Curncy', 'GBP', 'OIS', '1Y', 365, 'GBP_OIS', 'GBP OIS 1Y'),
        
        # JPY missing: 1W, 2W, 1Y
        ('JPY001W Index', 'JPY', 'RATE', '1W', 7, 'JPY_OIS', 'JPY 1W Rate'),
        ('JPY002W Index', 'JPY', 'RATE', '2W', 14, 'JPY_OIS', 'JPY 2W Rate'),
        ('JYSO1 Curncy', 'JPY', 'OIS', '1Y', 365, 'JPY_OIS', 'JPY OIS 1Y'),
        
        # CHF missing: 1W, 2W, 6M, 9M, 3Y, 4Y, 7Y, 15Y, 20Y, 30Y
        ('CHF001W Index', 'CHF', 'RATE', '1W', 7, 'CHF_OIS', 'CHF 1W Rate'),
        ('CHF002W Index', 'CHF', 'RATE', '2W', 14, 'CHF_OIS', 'CHF 2W Rate'),
        ('CHF006M Index', 'CHF', 'RATE', '6M', 180, 'CHF_OIS', 'CHF 6M Rate'),
        ('CHF009M Index', 'CHF', 'RATE', '9M', 270, 'CHF_OIS', 'CHF 9M Rate'),
        ('SFSO3 Curncy', 'CHF', 'OIS', '3Y', 1095, 'CHF_OIS', 'CHF OIS 3Y'),
        ('SFSO4 Curncy', 'CHF', 'OIS', '4Y', 1460, 'CHF_OIS', 'CHF OIS 4Y'),
        ('SFSO7 Curncy', 'CHF', 'OIS', '7Y', 2555, 'CHF_OIS', 'CHF OIS 7Y'),
        ('SFSO15 Curncy', 'CHF', 'OIS', '15Y', 5475, 'CHF_OIS', 'CHF OIS 15Y'),
        ('SFSO20 Curncy', 'CHF', 'OIS', '20Y', 7300, 'CHF_OIS', 'CHF OIS 20Y'),
        ('SFSO30 Curncy', 'CHF', 'OIS', '30Y', 9999, 'CHF_OIS', 'CHF OIS 30Y'),
        
        # CAD missing: 1W, 2W, 1Y
        ('CAD001W Index', 'CAD', 'RATE', '1W', 7, 'CAD_OIS', 'CAD 1W Rate'),
        ('CAD002W Index', 'CAD', 'RATE', '2W', 14, 'CAD_OIS', 'CAD 2W Rate'),
        ('CDSO1 Curncy', 'CAD', 'OIS', '1Y', 365, 'CAD_OIS', 'CAD OIS 1Y'),
        
        # AUD missing: 1W, 2W, 1Y
        ('AUD001W Index', 'AUD', 'RATE', '1W', 7, 'AUD_OIS', 'AUD 1W Rate'),
        ('AUD002W Index', 'AUD', 'RATE', '2W', 14, 'AUD_OIS', 'AUD 2W Rate'),
        ('ADSO1 Curncy', 'AUD', 'OIS', '1Y', 365, 'AUD_OIS', 'AUD OIS 1Y'),
        
        # NZD missing: 1W, 2W, 1Y
        ('NZD001W Index', 'NZD', 'RATE', '1W', 7, 'NZD_OIS', 'NZD 1W Rate'),
        ('NZD002W Index', 'NZD', 'RATE', '2W', 14, 'NZD_OIS', 'NZD 2W Rate'),
        ('NDSO1 Curncy', 'NZD', 'OIS', '1Y', 365, 'NZD_OIS', 'NZD OIS 1Y'),
        
        # SEK missing: 2W, 2M, 3M, 6M, 9M, 1Y, 30Y
        ('SEK002W Index', 'SEK', 'RATE', '2W', 14, 'SEK_IRS', 'SEK 2W Rate'),
        ('SEK002M Index', 'SEK', 'RATE', '2M', 60, 'SEK_IRS', 'SEK 2M Rate'),
        ('SEK003M Index', 'SEK', 'RATE', '3M', 90, 'SEK_IRS', 'SEK 3M Rate'),
        ('SEK006M Index', 'SEK', 'RATE', '6M', 180, 'SEK_IRS', 'SEK 6M Rate'),
        ('SEK009M Index', 'SEK', 'RATE', '9M', 270, 'SEK_IRS', 'SEK 9M Rate'),
        ('SKSW1 Curncy', 'SEK', 'IRS', '1Y', 365, 'SEK_IRS', 'SEK IRS 1Y'),
        ('SKSW30 Curncy', 'SEK', 'IRS', '30Y', 9999, 'SEK_IRS', 'SEK IRS 30Y'),
        
        # NOK missing: 2W, 2M, 3M, 6M, 9M, 1Y, 30Y
        ('NOK002W Index', 'NOK', 'RATE', '2W', 14, 'NOK_IRS', 'NOK 2W Rate'),
        ('NOK002M Index', 'NOK', 'RATE', '2M', 60, 'NOK_IRS', 'NOK 2M Rate'),
        ('NOK003M Index', 'NOK', 'RATE', '3M', 90, 'NOK_IRS', 'NOK 3M Rate'),
        ('NOK006M Index', 'NOK', 'RATE', '6M', 180, 'NOK_IRS', 'NOK 6M Rate'),
        ('NOK009M Index', 'NOK', 'RATE', '9M', 270, 'NOK_IRS', 'NOK 9M Rate'),
        ('NKSW1 Curncy', 'NOK', 'IRS', '1Y', 365, 'NOK_IRS', 'NOK IRS 1Y'),
        ('NKSW30 Curncy', 'NOK', 'IRS', '30Y', 9999, 'NOK_IRS', 'NOK IRS 30Y'),
    ]
    
    added = 0
    for ticker, currency, category, tenor, tenor_numeric, curve_name, description in missing_tenors:
        try:
            cursor.execute('''
                INSERT INTO bloomberg_tickers (bloomberg_ticker, currency_code, category, tenor, tenor_numeric, curve_name, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (ticker, currency, category, tenor, tenor_numeric, curve_name, description))
            added += 1
            print(f'✓ Added {ticker} - {tenor}')
        except:
            print(f'✗ {ticker} already exists')
    
    conn.commit()
    print(f'\nAdded {added} missing standard tenors')
    
    cursor.close()
    conn.close()

def fix_orphaned_tickers():
    """Assign orphaned tickers to their appropriate curves"""
    conn = psycopg2.connect(**conn_params)
    cursor = conn.cursor()
    
    print("\nFIXING ORPHANED TICKERS")
    print("=" * 60)
    
    # Get orphaned tickers and assign them to curves based on patterns
    cursor.execute("""
        SELECT bloomberg_ticker, currency_code, tenor, tenor_numeric
        FROM bloomberg_tickers 
        WHERE curve_name IS NULL AND currency_code IN ('USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD', 'SEK', 'NOK')
        ORDER BY currency_code, tenor_numeric
    """)
    
    orphaned = cursor.fetchall()
    updated = 0
    
    for ticker, currency, tenor, tenor_numeric in orphaned:
        curve_name = None
        category = None
        
        # Determine curve assignment based on ticker pattern
        if 'SO' in ticker and 'Curncy' in ticker:
            # OIS swaps
            curve_name = f'{currency}_OIS'
            category = 'OIS'
        elif 'SW' in ticker and 'Curncy' in ticker:
            # IRS swaps (SEK, NOK)
            curve_name = f'{currency}_IRS' 
            category = 'IRS'
        elif 'Index' in ticker:
            # Money market rates
            if currency in ['SEK', 'NOK']:
                curve_name = f'{currency}_IRS'
                category = 'RATE'
            else:
                curve_name = f'{currency}_OIS'
                category = 'RATE'
        
        if curve_name and category:
            cursor.execute("""
                UPDATE bloomberg_tickers 
                SET curve_name = %s, category = %s
                WHERE bloomberg_ticker = %s
            """, (curve_name, category, ticker))
            
            if cursor.rowcount > 0:
                updated += 1
                print(f'✓ Assigned {ticker} -> {curve_name}')
    
    conn.commit()
    print(f'\nAssigned {updated} orphaned tickers to curves')
    
    cursor.close()
    conn.close()

def final_cleanup():
    """Final cleanup and validation"""
    conn = psycopg2.connect(**conn_params)
    cursor = conn.cursor()
    
    print("\nFINAL CLEANUP & VALIDATION")
    print("=" * 60)
    
    # Remove any remaining duplicates
    cursor.execute("""
        WITH duplicates AS (
            SELECT bloomberg_ticker, currency_code, tenor_numeric,
                   ROW_NUMBER() OVER (PARTITION BY currency_code, tenor_numeric ORDER BY bloomberg_ticker) as rn
            FROM bloomberg_tickers 
            WHERE curve_name IS NOT NULL
        )
        DELETE FROM bloomberg_tickers 
        WHERE bloomberg_ticker IN (
            SELECT bloomberg_ticker FROM duplicates WHERE rn > 1
        )
    """)
    
    if cursor.rowcount > 0:
        print(f'✓ Removed {cursor.rowcount} remaining duplicate tickers')
    
    # Final coverage report
    currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD', 'SEK', 'NOK']
    
    print('\nFINAL COVERAGE REPORT:')
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
    
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    print("COMPREHENSIVE G10 CURRENCIES FIX")
    print("=" * 80)
    
    add_missing_standard_tenors()
    fix_orphaned_tickers()
    final_cleanup()
    
    print("\n" + "=" * 80)
    print("ALL FIXES COMPLETE - G10 CURVES OPTIMIZED")