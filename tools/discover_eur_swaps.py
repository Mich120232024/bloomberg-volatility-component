#!/usr/bin/env python3
import requests
import json

bloomberg_url = "http://20.172.249.92:8080"

print("Discovering EUR swap/OIS tickers...")
print("=" * 60)

# Try different search patterns for EUR swaps
search_patterns = [
    # EUR swap patterns
    {"pattern": "EUSWEA", "description": "EUR Swap Annual"},
    {"pattern": "EUSWEC", "description": "EUR Swap Semi-Annual"}, 
    {"pattern": "EUSWEE", "description": "EUR Swap ESTR"},
    {"pattern": "YCSW0045", "description": "Bloomberg EUR Swap Curve"},
    {"pattern": "EONIA", "description": "EONIA (legacy)"},
    {"pattern": "ESTRON", "description": "ESTR Overnight"},
    {"pattern": "EUR0001W", "description": "EUR 1 Week"},
    {"pattern": "EUR0002W", "description": "EUR 2 Week"},
    {"pattern": "EUSWE", "description": "EUR Swap ESTR basis"},
    {"pattern": "EUROIS", "description": "EUR OIS"},
]

valid_tickers = []

for search in search_patterns:
    print(f"\nTrying pattern: {search['pattern']} - {search['description']}")
    
    # Try with Index suffix
    ticker = f"{search['pattern']} Index"
    response = requests.post(
        f"{bloomberg_url}/api/bloomberg/reference",
        headers={"Authorization": "Bearer test"},
        json={
            "securities": [ticker],
            "fields": ["PX_LAST", "DESCRIPTION", "NAME", "CRNCY"]
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        if ticker in data and data[ticker].get("PX_LAST") is not None:
            rate = data[ticker]["PX_LAST"]
            desc = data[ticker].get("DESCRIPTION", "")
            if -5 < rate < 10:  # Reasonable rate range
                print(f"  ✓ Found: {ticker} = {rate:.4f}% - {desc}")
                valid_tickers.append(ticker)
    
    # Try with Curncy suffix
    ticker = f"{search['pattern']} Curncy"
    response = requests.post(
        f"{bloomberg_url}/api/bloomberg/reference",
        headers={"Authorization": "Bearer test"},
        json={
            "securities": [ticker],
            "fields": ["PX_LAST", "DESCRIPTION", "NAME", "CRNCY"]
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        if ticker in data and data[ticker].get("PX_LAST") is not None:
            rate = data[ticker]["PX_LAST"]
            desc = data[ticker].get("DESCRIPTION", "")
            if -5 < rate < 10:  # Reasonable rate range
                print(f"  ✓ Found: {ticker} = {rate:.4f}% - {desc}")
                valid_tickers.append(ticker)

# Try specific tenor patterns for EUR swaps
print("\n" + "=" * 60)
print("Trying EUR swap tenor patterns...")

tenors = ["1Y", "2Y", "3Y", "4Y", "5Y", "7Y", "10Y", "15Y", "20Y", "30Y"]
prefixes = ["EUSWEA", "EUSWEC", "EUSWE"]

for prefix in prefixes:
    print(f"\nChecking {prefix} pattern:")
    found_any = False
    
    for tenor in tenors:
        # Extract numeric part from tenor
        tenor_num = tenor.replace("Y", "")
        
        # Try different ticker formats
        tickers_to_try = [
            f"{prefix}{tenor_num} Curncy",
            f"{prefix}{tenor} Curncy",
            f"{prefix}{tenor_num} Index",
            f"{prefix}{tenor} Index"
        ]
        
        for ticker in tickers_to_try:
            response = requests.post(
                f"{bloomberg_url}/api/bloomberg/reference",
                headers={"Authorization": "Bearer test"},
                json={
                    "securities": [ticker],
                    "fields": ["PX_LAST", "DESCRIPTION"]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if ticker in data and data[ticker].get("PX_LAST") is not None:
                    rate = data[ticker]["PX_LAST"]
                    if -5 < rate < 10:
                        desc = data[ticker].get("DESCRIPTION", "")
                        print(f"  ✓ {ticker}: {rate:.4f}% - {desc}")
                        valid_tickers.append(ticker)
                        found_any = True
                        break
    
    if not found_any:
        print(f"  No valid tickers found for {prefix}")

print("\n" + "=" * 60)
print(f"Summary: Found {len(set(valid_tickers))} unique valid EUR swap/OIS tickers")
for ticker in sorted(set(valid_tickers)):
    print(f"  {ticker}")