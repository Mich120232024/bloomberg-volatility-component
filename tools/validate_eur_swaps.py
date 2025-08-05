#!/usr/bin/env python3
import requests

bloomberg_url = "http://20.172.249.92:8080"

# Test a few EUR swap tickers to understand what they actually contain
test_tickers = [
    "ESTR Index",
    "EUR001W Index", 
    "EUR006M Index",
    "EUSWEA1 Curncy",
    "EUSWEA20 Curncy",
    "YCSW0045 Index"
]

print("Validating EUR swap tickers with detailed fields...")
print("=" * 60)

for ticker in test_tickers:
    response = requests.post(
        f"{bloomberg_url}/api/bloomberg/reference",
        headers={"Authorization": "Bearer test"},
        json={
            "securities": [ticker],
            "fields": [
                "PX_LAST", 
                "DESCRIPTION", 
                "NAME",
                "SECURITY_TYP",
                "CRNCY",
                "ID_BB_GLOBAL",
                "TICKER"
            ]
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        if ticker in data:
            ticker_data = data[ticker]
            print(f"\n{ticker}:")
            for field, value in ticker_data.items():
                print(f"  {field:15}: {value}")
        else:
            print(f"\n{ticker}: No data returned")
    else:
        print(f"\n{ticker}: Error {response.status_code}")

# Also validate using the ticker validation endpoint
print("\n" + "=" * 60)
print("Batch validation of EUR tickers...")
print("=" * 60)

validation_response = requests.post(
    f"{bloomberg_url}/api/bloomberg/validate-tickers",
    headers={"Authorization": "Bearer test"},
    json=test_tickers
)

if validation_response.status_code == 200:
    results = validation_response.json()
    for ticker, info in results.items():
        print(f"\n{ticker}:")
        print(f"  Valid: {info.get('valid', False)}")
        print(f"  Price: {info.get('px_last', 'N/A')}")
        print(f"  Type: {info.get('security_type', 'N/A')}")
        print(f"  Description: {info.get('description', 'N/A')}")