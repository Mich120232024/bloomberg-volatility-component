#!/usr/bin/env python3
"""
Systematically discover ALL swap ticker patterns for all currencies
"""

import requests
import json
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from yield_curve_db_endpoint import get_database_connection

BLOOMBERG_API_URL = "http://20.172.249.92:8080"
HEADERS = {
    "Authorization": "Bearer test",
    "Content-Type": "application/json"
}

# Currency patterns for swap tickers
CURRENCY_PATTERNS = {
    'USD': ['USS', 'US', 'USD'],
    'EUR': ['EUR', 'EUS', 'EE'],
    'GBP': ['GBP', 'BPS', 'BP'],
    'JPY': ['JPY', 'JYS', 'JY'],
    'CHF': ['CHF', 'SFS', 'SF'],
    'CAD': ['CAD', 'CDS', 'CD'],
    'AUD': ['AUD', 'ADS', 'AD'],
    'NZD': ['NZD', 'NDS', 'ND'],
    'SEK': ['SEK', 'SKS', 'SK'],
    'NOK': ['NOK', 'NKS', 'NK'],
    'MXN': ['MXN', 'MXS', 'MP'],
    'ZAR': ['ZAR', 'ZAS', 'ZA'],
    'TRY': ['TRY', 'TRS', 'TR'],
    'CNH': ['CNH', 'CNS', 'CN'],
    'INR': ['INR', 'INS', 'IN'],
    'KRW': ['KRW', 'KRS', 'KR'],
    'TWD': ['TWD', 'TWS', 'TW'],
    'SGD': ['SGD', 'SGS', 'SG'],
    'HKD': ['HKD', 'HKS', 'HK'],
    'THB': ['THB', 'THS', 'TH'],
    'ILS': ['ILS', 'ILS', 'IL'],
    'PLN': ['PLN', 'PLS', 'PL'],
    'CZK': ['CZK', 'CZS', 'CZ'],
    'HUF': ['HUF', 'HUS', 'HU'],
    'RUB': ['RUB', 'RUS', 'RU'],
    'PHP': ['PHP', 'PHS', 'PH'],
    'DKK': ['DKK', 'DKS', 'DK'],
    'BRL': ['BRL', 'BRS', 'BR']
}

# Tenor patterns to test
TENOR_PATTERNS = ['1', '2', '3', '5', '7', '10', '15', '20', '25', '30']

# Swap type suffixes
SWAP_SUFFIXES = ['SW', 'S', 'W', 'IRD', 'IRS']

def test_ticker_pattern(currency, prefix, suffix, tenor):
    """Test if a ticker pattern is valid"""
    ticker = f"{prefix}{suffix}{tenor} Curncy"
    
    try:
        response = requests.post(
            f"{BLOOMBERG_API_URL}/api/bloomberg/reference",
            headers=HEADERS,
            json={
                "securities": [ticker],
                "fields": ["SECURITY_NAME", "PX_LAST"]
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            securities = data.get("data", {}).get("securities_data", [])
            
            if securities and securities[0].get("success"):
                name = securities[0].get("fields", {}).get("SECURITY_NAME", "")
                return True, name
        
        return False, None
            
    except Exception:
        return False, None

def discover_currency_swaps(currency):
    """Discover all swap tickers for a currency"""
    print(f"\n🔍 {currency}:")
    found_tickers = []
    
    prefixes = CURRENCY_PATTERNS.get(currency, [currency])
    
    for prefix in prefixes:
        for suffix in SWAP_SUFFIXES:
            for tenor in TENOR_PATTERNS:
                valid, name = test_ticker_pattern(currency, prefix, suffix, tenor)
                
                if valid:
                    ticker = f"{prefix}{suffix}{tenor} Curncy"
                    found_tickers.append({
                        'ticker': ticker,
                        'name': name,
                        'tenor': f"{tenor}Y",
                        'pattern': f"{prefix}{suffix}X"
                    })
                    print(f"  ✅ {ticker} - {name}")
                
                time.sleep(0.2)  # Rate limiting
    
    return found_tickers

def populate_database_with_swaps(all_discoveries):
    """Populate database with all discovered swap tickers"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        added_count = 0
        
        for currency, tickers in all_discoveries.items():
            if not tickers:
                continue
                
            print(f"\n📊 Adding {len(tickers)} {currency} swap tickers to database...")
            
            for ticker_data in tickers:
                ticker = ticker_data['ticker']
                tenor = ticker_data['tenor']
                
                # Insert into ticker_reference
                cursor.execute("""
                    INSERT INTO ticker_reference 
                    (bloomberg_ticker, currency_code, instrument_type, curve_name, is_active)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (bloomberg_ticker) DO NOTHING
                """, (ticker, currency, 'irs', f'{currency}_IRS', True))
                
                added_count += 1
        
        conn.commit()
        print(f"\n✅ Added {added_count} swap tickers to database")
        
        # Show final counts
        cursor.execute("""
            SELECT currency_code, instrument_type, COUNT(*) 
            FROM ticker_reference 
            WHERE instrument_type IN ('ois', 'irs')
            GROUP BY currency_code, instrument_type 
            ORDER BY currency_code, instrument_type
        """)
        
        print("\n=== DATABASE SUMMARY ===")
        for row in cursor.fetchall():
            print(f"{row[0]} {row[1].upper()}: {row[2]} tickers")
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        conn.rollback()
    finally:
        conn.close()

def main():
    """Discover swap patterns for all currencies"""
    print("=== SYSTEMATIC SWAP PATTERN DISCOVERY ===")
    
    all_discoveries = {}
    total_found = 0
    
    # Test all currencies
    currencies_to_test = list(CURRENCY_PATTERNS.keys())
    
    for currency in currencies_to_test:
        found_tickers = discover_currency_swaps(currency)
        
        if found_tickers:
            all_discoveries[currency] = found_tickers
            total_found += len(found_tickers)
            print(f"  📈 {currency}: {len(found_tickers)} swap tickers found")
        else:
            print(f"  ❌ {currency}: No swap tickers found")
    
    # Save discoveries
    with open('swap_pattern_discoveries.json', 'w') as f:
        json.dump(all_discoveries, f, indent=2)
    
    print(f"\n=== DISCOVERY COMPLETE ===")
    print(f"Currencies with swap data: {len(all_discoveries)}")
    print(f"Total swap tickers found: {total_found}")
    
    # Show summary by currency
    print(f"\n=== CURRENCY BREAKDOWN ===")
    for currency, tickers in all_discoveries.items():
        patterns = set(t['pattern'] for t in tickers)
        print(f"{currency}: {len(tickers)} tickers, patterns: {', '.join(patterns)}")
    
    # Populate database
    if all_discoveries:
        populate_database_with_swaps(all_discoveries)
    
    print("\n🎉 SWAP DISCOVERY COMPLETE!")

if __name__ == "__main__":
    main()