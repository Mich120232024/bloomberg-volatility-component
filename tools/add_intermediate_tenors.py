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

# Define intermediate tenors for each G10 currency
g10_intermediate_tenors = {
    'USD': {
        'curve_name': 'USD_OIS',
        'prefix': 'USSO',
        'suffix': 'Curncy',
        'tenors': [
            {'tenor': '12M', 'tenor_numeric': 365, 'description': 'USD OIS 12M'},
            {'tenor': '15M', 'tenor_numeric': 456, 'description': 'USD OIS 15M'},
            {'tenor': '18M', 'tenor_numeric': 548, 'description': 'USD OIS 18M'},
        ]
    },
    'EUR': {
        'curve_name': 'EUR_OIS',
        'prefix': 'EUSA',
        'suffix': 'Curncy',
        'tenors': [
            {'tenor': '12M', 'tenor_numeric': 365, 'description': 'EUR OIS 12M'},
            {'tenor': '15M', 'tenor_numeric': 456, 'description': 'EUR OIS 15M'},
            {'tenor': '18M', 'tenor_numeric': 548, 'description': 'EUR OIS 18M'},
        ]
    },
    'GBP': {
        'curve_name': 'GBP_OIS',
        'prefix': 'BPSO',
        'suffix': 'Curncy',
        'tenors': [
            {'tenor': '12M', 'tenor_numeric': 365, 'description': 'GBP OIS 12M'},
            {'tenor': '15M', 'tenor_numeric': 456, 'description': 'GBP OIS 15M'},
            {'tenor': '18M', 'tenor_numeric': 548, 'description': 'GBP OIS 18M'},
        ]
    },
    'JPY': {
        'curve_name': 'JPY_OIS',
        'prefix': 'JYSO',
        'suffix': 'Curncy',
        'tenors': [
            {'tenor': '12M', 'tenor_numeric': 365, 'description': 'JPY OIS 12M'},
            {'tenor': '15M', 'tenor_numeric': 456, 'description': 'JPY OIS 15M'},
            {'tenor': '18M', 'tenor_numeric': 548, 'description': 'JPY OIS 18M'},
        ]
    },
    'CHF': {
        'curve_name': 'CHF_OIS',
        'prefix': 'SFSO',
        'suffix': 'Curncy',
        'tenors': [
            {'tenor': '12M', 'tenor_numeric': 365, 'description': 'CHF OIS 12M'},
            {'tenor': '15M', 'tenor_numeric': 456, 'description': 'CHF OIS 15M'},
            {'tenor': '18M', 'tenor_numeric': 548, 'description': 'CHF OIS 18M'},
        ]
    },
    'CAD': {
        'curve_name': 'CAD_OIS',
        'prefix': 'CDSO',
        'suffix': 'Curncy',
        'tenors': [
            {'tenor': '12M', 'tenor_numeric': 365, 'description': 'CAD OIS 12M'},
            {'tenor': '15M', 'tenor_numeric': 456, 'description': 'CAD OIS 15M'},
            {'tenor': '18M', 'tenor_numeric': 548, 'description': 'CAD OIS 18M'},
        ]
    },
    'AUD': {
        'curve_name': 'AUD_OIS',
        'prefix': 'ADSO',
        'suffix': 'Curncy',
        'tenors': [
            {'tenor': '12M', 'tenor_numeric': 365, 'description': 'AUD OIS 12M'},
            {'tenor': '15M', 'tenor_numeric': 456, 'description': 'AUD OIS 15M'},
            {'tenor': '18M', 'tenor_numeric': 548, 'description': 'AUD OIS 18M'},
        ]
    },
    'NZD': {
        'curve_name': 'NZD_OIS',
        'prefix': 'NDSO',
        'suffix': 'Curncy',
        'tenors': [
            {'tenor': '12M', 'tenor_numeric': 365, 'description': 'NZD OIS 12M'},
            {'tenor': '15M', 'tenor_numeric': 456, 'description': 'NZD OIS 15M'},
            {'tenor': '18M', 'tenor_numeric': 548, 'description': 'NZD OIS 18M'},
        ]
    },
    'SEK': {
        'curve_name': 'SEK_IRS',
        'prefix': 'SKSW',
        'suffix': 'Curncy',
        'tenors': [
            {'tenor': '12M', 'tenor_numeric': 365, 'description': 'SEK IRS 12M'},
            {'tenor': '15M', 'tenor_numeric': 456, 'description': 'SEK IRS 15M'},
            {'tenor': '18M', 'tenor_numeric': 548, 'description': 'SEK IRS 18M'},
        ]
    },
    'NOK': {
        'curve_name': 'NOK_IRS',
        'prefix': 'NKSW',
        'suffix': 'Curncy',
        'tenors': [
            {'tenor': '12M', 'tenor_numeric': 365, 'description': 'NOK IRS 12M'},
            {'tenor': '15M', 'tenor_numeric': 456, 'description': 'NOK IRS 15M'},
            {'tenor': '18M', 'tenor_numeric': 548, 'description': 'NOK IRS 18M'},
        ]
    }
}

# Mapping for Bloomberg ticker construction
# For most: prefix + 12M/15M/18M + suffix
# Some might need special handling

conn = psycopg2.connect(**conn_params)
cursor = conn.cursor()

try:
    total_added = 0
    
    for currency, config in g10_intermediate_tenors.items():
        print(f"\n{'='*60}")
        print(f"Adding intermediate tenors for {currency}")
        print(f"{'='*60}")
        
        added_count = 0
        
        for tenor_info in config['tenors']:
            # Construct Bloomberg ticker
            # For 12M, 15M, 18M we need to check the pattern
            if tenor_info['tenor'] == '12M':
                ticker = f"{config['prefix']}1 {config['suffix']}"  # 1 year
            elif tenor_info['tenor'] == '15M':
                ticker = f"{config['prefix']}15M {config['suffix']}"  # 15 months
            elif tenor_info['tenor'] == '18M':
                ticker = f"{config['prefix']}18M {config['suffix']}"  # 18 months
            
            # Check if exists
            cursor.execute("""
                SELECT bloomberg_ticker FROM bloomberg_tickers 
                WHERE bloomberg_ticker = %s
            """, (ticker,))
            
            if cursor.fetchone():
                print(f"✓ {ticker} already exists - skipping")
            else:
                # Insert new ticker
                cursor.execute("""
                    INSERT INTO bloomberg_tickers (
                        bloomberg_ticker,
                        currency_code,
                        category,
                        tenor,
                        tenor_numeric,
                        curve_name,
                        description
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    ticker,
                    currency,
                    'OIS' if 'OIS' in config['curve_name'] else 'IRS',
                    tenor_info['tenor'],
                    tenor_info['tenor_numeric'],
                    config['curve_name'],
                    tenor_info['description']
                ))
                
                print(f"✓ Added {ticker} - {tenor_info['tenor']} - {tenor_info['description']}")
                added_count += 1
        
        print(f"Added {added_count} intermediate tenors for {currency}")
        total_added += added_count
    
    conn.commit()
    
    print(f"\n{'='*60}")
    print(f"✓ Total added: {total_added} intermediate tenors across all G10 currencies")
    
    # Show curves with new points
    print(f"\n{'='*60}")
    print("Updated curves (1-2Y range):")
    print(f"{'='*60}")
    
    for currency in ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD', 'SEK', 'NOK']:
        cursor.execute("""
            SELECT bloomberg_ticker, tenor, tenor_numeric
            FROM bloomberg_tickers
            WHERE currency_code = %s 
              AND tenor_numeric >= 365 
              AND tenor_numeric <= 730
            ORDER BY tenor_numeric
        """, (currency,))
        
        rows = cursor.fetchall()
        if rows:
            print(f"\n{currency}:")
            for ticker, tenor, tenor_numeric in rows:
                years = tenor_numeric / 365
                print(f"  {ticker:25} {tenor:>5} ({years:.2f}Y)")
        
except Exception as e:
    conn.rollback()
    print(f"✗ Error: {e}")
finally:
    cursor.close()
    conn.close()