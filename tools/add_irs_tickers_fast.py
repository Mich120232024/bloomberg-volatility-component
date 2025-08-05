#!/usr/bin/env python3
"""
Fast IRS ticker discovery for main G10 currencies
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

# Known working IRS patterns for major currencies
IRS_PATTERNS = {
    'USD': {
        'prefixes': ['USSW'],
        'tenors': ['1', '2', '3', '5', '7', '10', '15', '20', '25', '30']
    },
    'EUR': {
        'prefixes': ['EUSW', 'EURSW'],
        'tenors': ['1', '2', '3', '5', '7', '10', '15', '20', '25', '30']
    },
    'GBP': {
        'prefixes': ['BPSW', 'GBPSW'],
        'tenors': ['1', '2', '3', '5', '7', '10', '15', '20', '25', '30']
    },
    'JPY': {
        'prefixes': ['JYSW', 'JPYSW'],
        'tenors': ['1', '2', '3', '5', '7', '10', '15', '20', '25', '30']
    },
    'CHF': {
        'prefixes': ['SFSW', 'CHFSW'],
        'tenors': ['1', '2', '3', '5', '7', '10', '15', '20', '25', '30']
    },
    'CAD': {
        'prefixes': ['CDSW', 'CADSW'],
        'tenors': ['1', '2', '3', '5', '7', '10', '15', '20', '25', '30']
    },
    'AUD': {
        'prefixes': ['ADSW', 'AUDSW'],
        'tenors': ['1', '2', '3', '5', '7', '10', '15', '20', '25', '30']
    },
    'NZD': {
        'prefixes': ['NDSW', 'NZDSW'],
        'tenors': ['1', '2', '3', '5', '7', '10', '15', '20', '25', '30']
    },
    'SEK': {
        'prefixes': ['SKSW', 'SEKSW'],
        'tenors': ['1', '2', '3', '5', '7', '10', '15', '20', '25', '30']
    },
    'NOK': {
        'prefixes': ['NKSW', 'NOKSW'],
        'tenors': ['1', '2', '3', '5', '7', '10', '15', '20', '25', '30']
    }
}

def validate_batch_tickers(tickers):
    """Validate a batch of tickers quickly"""
    if not tickers:
        return []
    
    try:
        response = requests.post(
            f"{BLOOMBERG_API_URL}/api/bloomberg/reference",
            headers=HEADERS,
            json={
                "securities": tickers,
                "fields": ["SECURITY_NAME"]
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            securities = data.get("data", {}).get("securities_data", [])
            
            valid_tickers = []
            for sec in securities:
                if sec.get("success"):
                    valid_tickers.append({
                        'ticker': sec.get('security'),
                        'name': sec.get('fields', {}).get('SECURITY_NAME', '')
                    })
            
            return valid_tickers
        
        return []
            
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return []

def discover_irs_for_currency(currency):
    """Fast IRS discovery for one currency"""
    config = IRS_PATTERNS.get(currency)
    if not config:
        return []
    
    print(f"\n🔍 {currency} IRS:")
    
    # Generate all possible tickers for this currency
    test_tickers = []
    for prefix in config['prefixes']:
        for tenor in config['tenors']:
            test_tickers.append(f"{prefix}{tenor} Curncy")
    
    # Test in batches of 10
    valid_tickers = []
    batch_size = 10
    
    for i in range(0, len(test_tickers), batch_size):
        batch = test_tickers[i:i+batch_size]
        batch_results = validate_batch_tickers(batch)
        
        if batch_results:
            valid_tickers.extend(batch_results)
            for ticker_data in batch_results:
                print(f"  ✅ {ticker_data['ticker']} - {ticker_data['name']}")
        
        time.sleep(1)  # Rate limiting
    
    return valid_tickers

def main():
    """Fast IRS discovery for all G10"""
    print("=== FAST IRS TICKER DISCOVERY ===")
    
    all_irs_tickers = {}
    total_found = 0
    
    for currency in IRS_PATTERNS.keys():
        irs_tickers = discover_irs_for_currency(currency)
        
        if irs_tickers:
            all_irs_tickers[currency] = irs_tickers
            total_found += len(irs_tickers)
            print(f"  📈 {currency}: {len(irs_tickers)} IRS tickers")
        else:
            print(f"  ❌ {currency}: No IRS tickers found")
    
    print(f"\n=== DISCOVERY SUMMARY ===")
    print(f"Total IRS tickers found: {total_found}")
    
    # Save results
    with open('irs_discoveries.json', 'w') as f:
        json.dump(all_irs_tickers, f, indent=2)
    
    # Populate database
    if all_irs_tickers:
        print(f"\n📊 Populating database...")
        conn = get_database_connection()
        cursor = conn.cursor()
        
        try:
            added = 0
            for currency, tickers in all_irs_tickers.items():
                for ticker_data in tickers:
                    ticker = ticker_data['ticker']
                    
                    cursor.execute("""
                        INSERT INTO ticker_reference 
                        (bloomberg_ticker, currency_code, instrument_type, curve_name, is_active)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (bloomberg_ticker) DO NOTHING
                    """, (ticker, currency, 'irs', f'{currency}_IRS', True))
                    added += 1
            
            conn.commit()
            print(f"✅ Added {added} IRS tickers to database")
            
            # Show final database state
            cursor.execute("""
                SELECT currency_code, instrument_type, COUNT(*) 
                FROM ticker_reference 
                WHERE instrument_type IN ('ois', 'irs', 'OIS')
                GROUP BY currency_code, instrument_type 
                ORDER BY currency_code, instrument_type
            """)
            
            print(f"\n=== UPDATED DATABASE STATE ===")
            total_db_tickers = 0
            for row in cursor.fetchall():
                print(f"{row[0]} {row[1].upper()}: {row[2]} tickers")
                total_db_tickers += row[2]
            
            print(f"\nTotal database tickers: {total_db_tickers}")
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    print(f"\n🎉 IRS DISCOVERY COMPLETE!")

if __name__ == "__main__":
    main()