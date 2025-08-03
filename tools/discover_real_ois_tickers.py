#!/usr/bin/env python3
"""
Discover REAL OIS tickers using Bloomberg API for all tenors
"""

import requests
import json
import time

BLOOMBERG_API_URL = "http://20.172.249.92:8080"
HEADERS = {
    "Authorization": "Bearer test",
    "Content-Type": "application/json"
}

# Currencies to discover
CURRENCIES = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD', 'SEK', 'NOK', 'BRL']

def discover_ois_tickers(currency):
    """Discover real OIS tickers for a currency"""
    try:
        response = requests.post(
            f"{BLOOMBERG_API_URL}/api/bloomberg/ticker-discovery",
            headers=HEADERS,
            json={
                "search_type": "ois",
                "currency": currency,
                "max_results": 100  # Get all available
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("tickers", [])
        else:
            print(f"API error for {currency}: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"Error discovering {currency}: {e}")
        return []

def main():
    """Discover all real OIS tickers"""
    all_discoveries = {}
    
    for currency in CURRENCIES:
        print(f"\nDiscovering {currency} OIS tickers...")
        tickers = discover_ois_tickers(currency)
        
        if tickers:
            print(f"Found {len(tickers)} tickers:")
            # Group by tenor type
            by_type = {}
            for t in tickers:
                ticker = t.get('ticker', '')
                desc = t.get('description', '')
                tenor = t.get('tenor', 'Unknown')
                
                if 'SWAP' in desc.upper() or 'OIS' in desc.upper():
                    print(f"  {ticker} - {tenor} - {desc}")
                    by_type.setdefault(tenor, []).append(ticker)
            
            all_discoveries[currency] = by_type
        else:
            print(f"  No tickers found")
        
        time.sleep(2)  # Rate limiting
    
    # Save discoveries
    with open('discovered_ois_tickers.json', 'w') as f:
        json.dump(all_discoveries, f, indent=2)
    
    print(f"\nSaved discoveries to discovered_ois_tickers.json")

if __name__ == "__main__":
    main()