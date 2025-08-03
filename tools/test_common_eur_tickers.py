#!/usr/bin/env python3
import requests

bloomberg_url = "http://20.172.249.92:8080"

# Common EUR rate tickers based on market standards
test_tickers = [
    # ESTR rates
    "ESTR Index",
    "ESTRON Index",
    
    # EURIBOR rates
    "EUR001W Index",
    "EUR001M Index", 
    "EUR003M Index",
    "EUR006M Index",
    
    # EUR Swap rates - different patterns
    "EUSW1 Curncy",
    "EUSW2 Curncy",
    "EUSW5 Curncy",
    "EUSW10 Curncy",
    
    # EUR OIS
    "EUROIS1 Index",
    "EUROIS2 Index",
    
    # Alternative patterns
    "EUDR1T Curncy",
    "EUDR2T Curncy",
    
    # EUR vs ESTR swaps
    "EESW1 Curncy",
    "EESW2 Curncy",
    
    # Bloomberg curve
    "YCSW0045 Index"
]

print("Testing common EUR ticker patterns...")
print("=" * 60)

# Batch validate all tickers
response = requests.post(
    f"{bloomberg_url}/api/bloomberg/validate-tickers",
    headers={"Authorization": "Bearer test"},
    json=test_tickers
)

if response.status_code == 200:
    results = response.json()
    valid_tickers = []
    
    for ticker, info in results.items():
        if info.get('valid', False):
            print(f"✓ {ticker}: {info.get('px_last', 'N/A')} - {info.get('description', 'N/A')}")
            valid_tickers.append(ticker)
        else:
            print(f"✗ {ticker}: Invalid")
    
    print(f"\nFound {len(valid_tickers)} valid EUR tickers")
    
    # Get detailed info for valid tickers
    if valid_tickers:
        print("\nDetailed info for valid tickers:")
        print("=" * 60)
        
        for ticker in valid_tickers:
            ref_response = requests.post(
                f"{bloomberg_url}/api/bloomberg/reference",
                headers={"Authorization": "Bearer test"},
                json={
                    "securities": [ticker],
                    "fields": ["PX_LAST", "DESCRIPTION", "NAME", "CRNCY", "SECURITY_TYP"]
                }
            )
            
            if ref_response.status_code == 200:
                data = ref_response.json()
                if ticker in data:
                    print(f"\n{ticker}:")
                    for field, value in data[ticker].items():
                        print(f"  {field}: {value}")
else:
    print(f"Validation failed: {response.status_code}")
    print(response.text)