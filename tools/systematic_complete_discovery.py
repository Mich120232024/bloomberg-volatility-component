#!/usr/bin/env python3
"""
Systematic complete discovery of all available swap curves for all currencies
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

# All currencies to check
ALL_CURRENCIES = [
    'USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD', 'SEK', 'NOK',
    'MXN', 'ZAR', 'TRY', 'CNH', 'INR', 'KRW', 'TWD', 'SGD', 'HKD', 'THB', 
    'ILS', 'PLN', 'CZK', 'HUF', 'RUB', 'PHP', 'DKK', 'BRL'
]

# Known OIS reference rates based on research
REFERENCE_RATES = {
    'USD': ('SOFR', 'Secured Overnight Financing Rate'),
    'EUR': ('ESTR', 'Euro Short-Term Rate'),
    'GBP': ('SONIA', 'Sterling Overnight Index Average'),
    'JPY': ('TONAR', 'Tokyo Overnight Average Rate'),
    'CHF': ('SARON', 'Swiss Average Rate Overnight'),
    'CAD': ('CORRA', 'Canadian Overnight Repo Rate Average'),
    'AUD': ('AONIA', 'AUD Overnight Index Average'),
    'NZD': ('NZIONA', 'NZ Overnight Index Average'),
    'SEK': ('SWESTR', 'Swedish krona Short Term Rate'),
    'NOK': ('NOWA', 'Norwegian Overnight Weighted Average'),
    'DKK': ('DESTR', 'Denmark Short Term Rate'),
    'BRL': ('SELIC', 'Sistema Especial de Liquidação e Custódia')
}

def discover_ois_for_currency(currency):
    """Discover all available OIS tickers for a currency"""
    try:
        response = requests.post(
            f"{BLOOMBERG_API_URL}/api/bloomberg/ticker-discovery",
            headers=HEADERS,
            json={
                "search_type": "ois",
                "currency": currency,
                "max_results": 100
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("tickers", [])
        else:
            return []
            
    except Exception as e:
        print(f"❌ Error discovering {currency}: {e}")
        return []

def test_ticker_patterns(currency, patterns):
    """Test specific ticker patterns for a currency"""
    valid_tickers = []
    
    for pattern_batch in [patterns[i:i+10] for i in range(0, len(patterns), 10)]:
        try:
            response = requests.post(
                f"{BLOOMBERG_API_URL}/api/bloomberg/reference",
                headers=HEADERS,
                json={
                    "securities": pattern_batch,
                    "fields": ["SECURITY_NAME", "PX_LAST"]
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                securities = data.get("data", {}).get("securities_data", [])
                
                for sec in securities:
                    if sec.get("success"):
                        ticker = sec.get("security")
                        name = sec.get("fields", {}).get("SECURITY_NAME", "")
                        if 'OIS' in name.upper() or 'OVERNIGHT' in name.upper() or 'INDEX' in name.upper():
                            valid_tickers.append({
                                'ticker': ticker,
                                'name': name,
                                'currency': currency
                            })
                            print(f"  ✅ Found: {ticker} - {name}")
            
            time.sleep(1)  # Rate limiting
                
        except Exception as e:
            print(f"  ❌ Error testing patterns: {e}")
    
    return valid_tickers

def generate_ticker_patterns(currency):
    """Generate potential OIS ticker patterns based on currency"""
    patterns = []
    
    # Common prefixes for each currency
    prefix_map = {
        'USD': ['USS', 'USSO', 'SOFR'],
        'EUR': ['EUS', 'EESW', 'ESTR', 'EUR'],
        'GBP': ['BPS', 'SONIO', 'GBP'],
        'JPY': ['JYS', 'JYSO', 'JPY'],
        'CHF': ['SFS', 'SSARON', 'CHF'],
        'CAD': ['CDS', 'CDSO', 'CAD'],
        'AUD': ['ADS', 'RBAO', 'AUD'],
        'NZD': ['NDS', 'NDSO', 'NZD'],
        'SEK': ['SKS', 'SKSO', 'SEK'],
        'NOK': ['NKS', 'NKSO', 'NOK'],
        'DKK': ['DKS', 'DKSO', 'DKK'],
        'BRL': ['BRS', 'BRSO', 'BRL']
    }
    
    prefixes = prefix_map.get(currency, [currency[:2] + 'S', currency])
    
    # Common tenors
    monthly_tenors = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K']  # 1-11M
    yearly_tenors = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '12', '15', '18', '20', '25', '30']
    
    # Generate patterns
    for prefix in prefixes:
        # Monthly patterns (USSOA, USSOB, etc.)
        for tenor in monthly_tenors:
            patterns.append(f"{prefix}O{tenor} Curncy")
        
        # Yearly patterns (USSO1, USSO2, etc.)
        for tenor in yearly_tenors:
            patterns.append(f"{prefix}O{tenor} Curncy")
        
        # Special monthly patterns (15M, 18M, 21M)
        for tenor in ['15M', '18M', '21M']:
            patterns.append(f"{prefix}O{tenor} Curncy")
    
    # Overnight rates
    if currency in REFERENCE_RATES:
        rate_name, _ = REFERENCE_RATES[currency]
        patterns.extend([
            f"{rate_name} Index",
            f"{rate_name}RATE Index",
            f"{currency}ON Index"
        ])
    
    return patterns

def populate_database_complete(all_discoveries):
    """Populate database with all discovered tickers"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        # Clear existing data for clean start
        cursor.execute("DELETE FROM ticker_reference")
        print(f"Cleared existing ticker_reference data")
        
        total_added = 0
        
        for currency, tickers in all_discoveries.items():
            if not tickers:
                continue
                
            # Determine curve name based on reference rate
            rate_info = REFERENCE_RATES.get(currency, (currency, ''))
            curve_name = f"{currency}_{rate_info[0]}_OIS"
            
            print(f"\n📊 Adding {len(tickers)} {currency} tickers to database...")
            
            for ticker_data in tickers:
                ticker = ticker_data['ticker']
                
                # Determine instrument type
                inst_type = 'overnight' if 'Index' in ticker and 'RATE' in ticker else 'ois'
                
                cursor.execute("""
                    INSERT INTO ticker_reference 
                    (bloomberg_ticker, currency_code, instrument_type, curve_name, is_active)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (bloomberg_ticker) DO NOTHING
                """, (ticker, currency, inst_type, curve_name, True))
                
                total_added += 1
        
        conn.commit()
        print(f"\n✅ Successfully added {total_added} tickers to database")
        
        # Show final state by currency
        cursor.execute("""
            SELECT currency_code, COUNT(*), string_agg(DISTINCT instrument_type, ', ')
            FROM ticker_reference 
            GROUP BY currency_code 
            ORDER BY COUNT(*) DESC
        """)
        
        print("\n=== FINAL DATABASE STATE ===")
        grand_total = 0
        for row in cursor.fetchall():
            print(f"{row[0]}: {row[1]} tickers ({row[2]})")
            grand_total += row[1]
        
        print(f"\n🎉 TOTAL TICKERS IN DATABASE: {grand_total}")
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        conn.rollback()
    finally:
        conn.close()

def main():
    """Complete systematic discovery for all currencies"""
    print("=== SYSTEMATIC COMPLETE OIS DISCOVERY ===")
    
    all_discoveries = {}
    
    for currency in ALL_CURRENCIES:
        print(f"\n{'='*60}")
        print(f"🔍 {currency} - {REFERENCE_RATES.get(currency, ['Unknown', 'Unknown rate'])[1]}")
        print(f"{'='*60}")
        
        # First try discovery endpoint
        print(f"\n1. Testing discovery endpoint for {currency}...")
        discovered = discover_ois_for_currency(currency)
        
        if discovered:
            print(f"  📊 Discovery found {len(discovered)} tickers")
            all_discoveries[currency] = discovered
        else:
            print(f"  ❌ Discovery returned no results")
            
            # Try pattern-based search
            print(f"\n2. Testing pattern-based search for {currency}...")
            patterns = generate_ticker_patterns(currency)
            print(f"  📝 Testing {len(patterns)} patterns...")
            
            valid_tickers = test_ticker_patterns(currency, patterns)
            
            if valid_tickers:
                print(f"  ✅ Pattern search found {len(valid_tickers)} valid tickers")
                all_discoveries[currency] = valid_tickers
            else:
                print(f"  ❌ No valid OIS tickers found for {currency}")
        
        time.sleep(2)  # Rate limiting between currencies
    
    # Save complete discoveries
    with open('complete_ois_discoveries.json', 'w') as f:
        json.dump(all_discoveries, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"=== DISCOVERY COMPLETE ===")
    print(f"{'='*60}")
    print(f"Currencies with OIS data: {len(all_discoveries)}")
    
    # Show summary
    for currency, tickers in sorted(all_discoveries.items()):
        print(f"{currency}: {len(tickers)} tickers")
    
    # Populate database
    if all_discoveries:
        populate_database_complete(all_discoveries)
    
    print("\n🎉 SYSTEMATIC DISCOVERY AND POPULATION COMPLETE!")

if __name__ == "__main__":
    main()