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

def equalize_coverage():
    """Add missing standard tenors to bring all currencies to same coverage level"""
    conn = psycopg2.connect(**conn_params)
    cursor = conn.cursor()
    
    print("EQUALIZING G10 CURRENCY COVERAGE")
    print("=" * 80)
    
    # Standard tenor set based on USD/CAD/AUD coverage (30 tickers)
    standard_tenors = [
        ('O/N', 1),
        ('1W', 7), ('2W', 14), 
        ('1M', 30), ('2M', 60), ('3M', 90), ('6M', 180), ('9M', 270),
        ('1Y', 365), ('15M', 456), ('18M', 548), ('21M', 639), ('2Y', 730),
        ('3Y', 1095), ('4Y', 1460), ('5Y', 1825), ('6Y', 2190), ('7Y', 2555),
        ('8Y', 2920), ('9Y', 3285), ('10Y', 3650), ('12Y', 4380), ('15Y', 5475),
        ('20Y', 7300), ('25Y', 9125), ('30Y', 9999)
    ]
    
    # Currency-specific ticker patterns and curve types
    currency_config = {
        'EUR': {'prefix': 'EU', 'ois_pattern': 'EUSA{tenor}', 'rate_pattern': 'EUR{tenor:03d}', 'curve': 'EUR_OIS'},
        'GBP': {'prefix': 'BP', 'ois_pattern': 'BPSO{tenor}', 'rate_pattern': 'GBP{tenor:03d}', 'curve': 'GBP_OIS'},
        'JPY': {'prefix': 'JY', 'ois_pattern': 'JYSO{tenor}', 'rate_pattern': 'JPY{tenor:03d}', 'curve': 'JPY_OIS'},
        'CHF': {'prefix': 'SF', 'ois_pattern': 'SFSO{tenor}', 'rate_pattern': 'CHF{tenor:03d}', 'curve': 'CHF_OIS'},
        'SEK': {'prefix': 'SK', 'ois_pattern': 'SKSW{tenor}', 'rate_pattern': 'SEK{tenor:03d}', 'curve': 'SEK_IRS'},
        'NOK': {'prefix': 'NK', 'ois_pattern': 'NKSW{tenor}', 'rate_pattern': 'NOK{tenor:03d}', 'curve': 'NOK_IRS'},
        'NZD': {'prefix': 'ND', 'ois_pattern': 'NDSO{tenor}', 'rate_pattern': 'NZD{tenor:03d}', 'curve': 'NZD_OIS'},
    }
    
    added_total = 0
    
    for currency, config in currency_config.items():
        print(f"\n{currency}:")
        print("-" * 40)
        
        # Get existing tenors
        cursor.execute("""
            SELECT tenor_numeric FROM bloomberg_tickers 
            WHERE currency_code = %s AND curve_name IS NOT NULL
        """, (currency,))
        existing_tenors = {float(row[0]) for row in cursor.fetchall()}
        
        added_count = 0
        for tenor_name, days in standard_tenors:
            if days not in existing_tenors:
                # Generate ticker based on tenor
                if days <= 365:
                    # Short tenors use rate pattern
                    if days == 1:
                        ticker = f"{currency}DR1T Curncy"  # Overnight
                    elif days == 7:
                        ticker = f"{currency}001W Index"
                    elif days == 14:
                        ticker = f"{currency}002W Index"
                    elif days == 30:
                        ticker = f"{currency}001M Index"
                    elif days == 60:
                        ticker = f"{currency}002M Index"
                    elif days == 90:
                        ticker = f"{currency}003M Index"
                    elif days == 180:
                        ticker = f"{currency}006M Index"
                    elif days == 270:
                        ticker = f"{currency}009M Index"
                    elif days == 365:
                        # 1Y uses OIS pattern
                        ticker = config['ois_pattern'].format(tenor='1')
                        if currency in ['SEK', 'NOK']:
                            ticker = ticker.replace('SO', 'SW')
                        ticker += ' Curncy'
                    else:
                        # Intermediate tenors
                        if days == 456:  # 15M
                            ticker = config['ois_pattern'].format(tenor='1C') + ' Curncy'
                        elif days == 548:  # 18M  
                            ticker = config['ois_pattern'].format(tenor='1F') + ' Curncy'
                        elif days == 639:  # 21M
                            ticker = config['ois_pattern'].format(tenor='1I') + ' Curncy'
                        else:
                            continue
                        if currency in ['SEK', 'NOK']:
                            ticker = ticker.replace('SO', 'SW')
                else:
                    # Long tenors use OIS/IRS pattern
                    years = int(days / 365)
                    ticker = config['ois_pattern'].format(tenor=years)
                    if currency in ['SEK', 'NOK']:
                        ticker = ticker.replace('SO', 'SW')
                    ticker += ' Curncy'
                
                # Determine category
                category = 'IRS' if currency in ['SEK', 'NOK'] else 'OIS'
                if days < 365:
                    category = 'RATE'
                
                try:
                    cursor.execute("""
                        INSERT INTO bloomberg_tickers (
                            bloomberg_ticker, currency_code, category, tenor, 
                            tenor_numeric, curve_name, description
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        ticker, currency, category, tenor_name, 
                        days, config['curve'], f"{currency} {category} {tenor_name}"
                    ))
                    print(f"✓ Added {ticker} - {tenor_name}")
                    added_count += 1
                    added_total += 1
                except Exception as e:
                    conn.rollback()
                    print(f"✗ {ticker} already exists or invalid: {e}")
        
        print(f"Added {added_count} tickers for {currency}")
    
    conn.commit()
    print(f"\n✓ Total added: {added_total} tickers")
    
    # Final coverage report
    print("\nFINAL EQUALIZED COVERAGE:")
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
    equalize_coverage()