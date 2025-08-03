#!/usr/bin/env python3
import requests
import json

# Verify current EUR tickers to understand the data issue
gateway_url = "http://localhost:8000"
bloomberg_url = "http://20.172.249.92:8080"

# List of EUR tickers from the database
eur_tickers = [
    "ESTR Index",
    "EUR001M Index", "EUR002M Index", "EUR003M Index", 
    "EUR006M Index", "EUR012M Index",
    "EESWE1 Curncy", "EESWE2 Curncy", "EESWE3 Curncy",
    "EESWE4 Curncy", "EESWE5 Curncy", "EESWE10 Curncy",
    "EESWE15 Curncy", "EESWE20 Curncy", "EESWE30 Curncy"
]

print("Verifying EUR tickers with Bloomberg API...")
print("=" * 60)

# Verify each ticker individually
for ticker in eur_tickers:
    response = requests.post(
        f"{bloomberg_url}/api/bloomberg/reference",
        headers={"Authorization": "Bearer test"},
        json={
            "securities": [ticker],
            "fields": ["PX_LAST", "DESCRIPTION", "NAME", "CRNCY", "SECURITY_TYP"]
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        if data and ticker in data:
            ticker_data = data[ticker]
            print(f"\n{ticker}:")
            print(f"  PX_LAST: {ticker_data.get('PX_LAST', 'N/A')}")
            print(f"  NAME: {ticker_data.get('NAME', 'N/A')}")
            print(f"  DESCRIPTION: {ticker_data.get('DESCRIPTION', 'N/A')}")
            print(f"  CRNCY: {ticker_data.get('CRNCY', 'N/A')}")
            print(f"  SECURITY_TYP: {ticker_data.get('SECURITY_TYP', 'N/A')}")
    else:
        print(f"\nError fetching {ticker}: {response.status_code}")

# Now verify ticker discovery for EUR OIS
print("\n" + "=" * 60)
print("Discovering EUR OIS tickers using Bloomberg discovery endpoint...")
print("=" * 60)

discovery_response = requests.post(
    f"{bloomberg_url}/api/bloomberg/ticker-discovery",
    headers={"Authorization": "Bearer test"},
    json={
        "search_type": "ois",
        "currency": "EUR",
        "max_results": 50
    }
)

if discovery_response.status_code == 200:
    discovered = discovery_response.json()
    if "tickers" in discovered:
        print(f"\nFound {len(discovered['tickers'])} EUR OIS tickers:")
        for ticker_info in discovered['tickers']:
            print(f"  {ticker_info['ticker']}: {ticker_info.get('description', 'N/A')}")
else:
    print(f"Discovery failed: {discovery_response.status_code}")
    print(discovery_response.text)

# Verify well-known EUR swap curve ticker
print("\n" + "=" * 60)
print("Verifying well-known EUR swap curve ticker...")
print("=" * 60)

eur_swap_ticker = "YCSW0045 Index"
response = requests.post(
    f"{bloomberg_url}/api/bloomberg/reference",
    headers={"Authorization": "Bearer test"},
    json={
        "securities": [eur_swap_ticker],
        "fields": ["PX_LAST", "DESCRIPTION", "NAME", "CRNCY", "SECURITY_TYP"]
    }
)

if response.status_code == 200:
    data = response.json()
    if data and eur_swap_ticker in data:
        ticker_data = data[eur_swap_ticker]
        print(f"\n{eur_swap_ticker}:")
        print(f"  PX_LAST: {ticker_data.get('PX_LAST', 'N/A')}")
        print(f"  NAME: {ticker_data.get('NAME', 'N/A')}")
        print(f"  DESCRIPTION: {ticker_data.get('DESCRIPTION', 'N/A')}")