#!/usr/bin/env python3
"""
Discover OIS/swap tickers for emerging market currencies using Bloomberg API
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

# EM currencies to discover
EM_CURRENCIES = [
    'MXN', 'ZAR', 'TRY', 'CNH', 'INR', 'KRW', 'TWD', 
    'SGD', 'HKD', 'THB', 'ILS', 'PLN', 'CZK', 'HUF', 
    'RUB', 'PHP', 'DKK'
]

# Known overnight rates for EM currencies
OVERNIGHT_RATES = {
    'MXN': 'MXONBR Index',    # Mexican overnight rate
    'ZAR': 'ZARONIA Index',    # South African overnight rate
    'TRY': 'TRTONRA Index',    # Turkish overnight rate
    'CNH': 'CNHHIBOR Index',   # Offshore CNH rate
    'INR': 'MIBOR Index',      # Mumbai interbank rate
    'KRW': 'KWCDC Index',      # Korean rate
    'SGD': 'SIBORON Index',    # Singapore overnight rate
    'HKD': 'HIHBOR Index',     # Hong Kong overnight rate
    'THB': 'THBFIX Index',     # Thai fixing rate
    'ILS': 'TELBOR Index',     # Tel Aviv interbank rate
    'PLN': 'WIBOR Index',      # Warsaw interbank rate
    'CZK': 'PRIBOR Index',     # Prague interbank rate
    'HUF': 'BUBOR Index',      # Budapest interbank rate
    'RUB': 'RUONIA Index',     # Russian overnight rate
    'DKK': 'CIBOR Index'       # Copenhagen interbank rate
}

def search_currency_swaps(currency):
    """Search for swap/OIS tickers for a currency"""
    found_tickers = []
    
    # Try different search patterns
    search_patterns = [
        f"{currency} OIS",
        f"{currency} swap",
        f"{currency} overnight index swap",
        f"{currency}SO",  # Common OIS pattern
        f"{currency}SW"   # Common swap pattern
    ]
    
    for pattern in search_patterns:
        try:
            # Use reference data search
            response = requests.post(
                f"{BLOOMBERG_API_URL}/api/bloomberg/reference",
                headers=HEADERS,
                json={
                    "securities": [f"{pattern}* Curncy"],
                    "fields": ["SECURITY_NAME", "CRNCY", "PX_LAST"]
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                securities = data.get("data", {}).get("securities_data", [])
                
                for sec in securities:
                    if sec.get("success"):
                        ticker = sec.get("security", "")
                        name = sec.get("fields", {}).get("SECURITY_NAME", "")
                        
                        # Filter for OIS/swap instruments
                        if any(term in name.upper() for term in ["OIS", "OVERNIGHT", "SWAP", "SOFR", "SONIA"]):
                            found_tickers.append({
                                "ticker": ticker,
                                "name": name,
                                "pattern": pattern
                            })
            
            time.sleep(0.5)  # Rate limiting
            
        except Exception as e:
            print(f"Error searching {pattern}: {e}")
    
    return found_tickers

def validate_ticker(ticker):
    """Validate ticker returns real data"""
    try:
        response = requests.post(
            f"{BLOOMBERG_API_URL}/api/bloomberg/market-data",
            headers=HEADERS,
            json={
                "securities": [ticker],
                "fields": ["PX_LAST", "SECURITY_NAME"]
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            securities = data.get("data", {}).get("securities_data", [])
            
            if securities and securities[0].get("success"):
                fields = securities[0].get("fields", {})
                return True, fields
        
        return False, None
            
    except Exception as e:
        return False, str(e)

def main():
    """Discover EM currency OIS tickers"""
    discoveries = {}
    
    print("=== DISCOVERING EM CURRENCY OIS/SWAP TICKERS ===")
    
    for currency in EM_CURRENCIES:
        print(f"\n{currency}:")
        
        # First check overnight rate
        overnight = OVERNIGHT_RATES.get(currency)
        if overnight:
            valid, data = validate_ticker(overnight)
            if valid:
                print(f"  ✅ Overnight: {overnight} - {data.get('SECURITY_NAME', 'N/A')}")
            else:
                print(f"  ❌ Overnight: {overnight} - Invalid")
        
        # Search for swap/OIS tickers
        found = search_currency_swaps(currency)
        
        if found:
            print(f"  Found {len(found)} potential tickers:")
            
            valid_tickers = []
            for item in found[:10]:  # Limit to first 10 to avoid too many requests
                ticker = item["ticker"]
                valid, data = validate_ticker(ticker)
                
                if valid:
                    print(f"  ✅ {ticker} - {item['name']}")
                    valid_tickers.append({
                        "ticker": ticker,
                        "name": item["name"],
                        "last_price": data.get("PX_LAST", "N/A")
                    })
                
                time.sleep(0.5)
            
            if valid_tickers:
                discoveries[currency] = {
                    "overnight": overnight if overnight else None,
                    "swaps": valid_tickers
                }
        else:
            print(f"  No OIS/swap tickers found")
        
        time.sleep(2)  # Rate limiting between currencies
    
    # Save discoveries
    with open('discovered_em_ois_tickers.json', 'w') as f:
        json.dump(discoveries, f, indent=2)
    
    print(f"\n=== SUMMARY ===")
    print(f"Discovered tickers for {len(discoveries)} currencies")
    print("Saved to discovered_em_ois_tickers.json")
    
    # Update ticker_reference with discovered tickers
    if discoveries:
        print("\nUpdating ticker_reference...")
        conn = get_database_connection()
        cursor = conn.cursor()
        
        try:
            added = 0
            for currency, data in discoveries.items():
                # Add overnight rate
                if data.get("overnight"):
                    cursor.execute("""
                        INSERT INTO ticker_reference 
                        (bloomberg_ticker, currency_code, instrument_type, curve_name, is_active)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (bloomberg_ticker) DO NOTHING
                    """, (data["overnight"], currency, 'overnight', f'{currency}_OIS', True))
                    added += 1
                
                # Add swap tickers
                for swap in data.get("swaps", []):
                    cursor.execute("""
                        INSERT INTO ticker_reference 
                        (bloomberg_ticker, currency_code, instrument_type, curve_name, is_active)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (bloomberg_ticker) DO NOTHING
                    """, (swap["ticker"], currency, 'swap', f'{currency}_OIS', True))
                    added += 1
            
            conn.commit()
            print(f"Added {added} new tickers to ticker_reference")
            
        except Exception as e:
            print(f"Database error: {e}")
            conn.rollback()
        finally:
            conn.close()

if __name__ == "__main__":
    main()