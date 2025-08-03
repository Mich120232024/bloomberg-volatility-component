#!/usr/bin/env python3
import requests

bloomberg_url = "http://20.172.249.92:8080"

# Test various EUR swap ticker patterns for long end
test_patterns = [
    # EUR IRS vs 6M EURIBOR
    ("EUSA", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20, 25, 30]),
    ("EUSW", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20, 25, 30]),
    ("EUSWAB", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20, 25, 30]),
    ("EURAB", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20, 25, 30]),
    
    # EUR vs 3M EURIBOR
    ("EUSC", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20, 25, 30]),
    ("EUSWEC", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20, 25, 30]),
    
    # EUR OIS
    ("EOIS", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20, 25, 30]),
    ("EUROIS", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20, 25, 30]),
    
    # Alternative patterns
    ("S0045", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20, 25, 30]),
    ("EUR", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20, 25, 30])
]

suffixes = ["Curncy", "Index", "Comdty"]

print("Searching for EUR long-end swap tickers...")
print("=" * 60)

found_tickers = []

for prefix, tenors in test_patterns:
    print(f"\nTesting {prefix} pattern...")
    pattern_found = False
    
    for tenor in tenors:
        if pattern_found and tenor > 5:  # Skip testing all tenors if pattern works
            continue
            
        for suffix in suffixes:
            # Try different formatting
            tickers_to_test = [
                f"{prefix}{tenor} {suffix}",      # EUSA1 Curncy
                f"{prefix}{tenor}Y {suffix}",     # EUSA1Y Curncy
                f"{prefix}0{tenor} {suffix}" if tenor < 10 else f"{prefix}{tenor} {suffix}",  # EUSA01 Curncy
            ]
            
            for ticker in tickers_to_test:
                response = requests.post(
                    f"{bloomberg_url}/api/bloomberg/reference",
                    headers={"Authorization": "Bearer test"},
                    json={
                        "securities": [ticker],
                        "fields": ["PX_LAST", "DESCRIPTION", "NAME"]
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "data" in data and "securities_data" in data["data"]:
                        for sec_data in data["data"]["securities_data"]:
                            if sec_data.get("fields", {}).get("PX_LAST") is not None:
                                rate = sec_data["fields"]["PX_LAST"]
                                if -5 < rate < 10:  # Reasonable rate range
                                    desc = sec_data["fields"].get("NAME", "")
                                    print(f"  ✓ {ticker}: {rate:.4f}% - {desc}")
                                    found_tickers.append((ticker, tenor, rate))
                                    pattern_found = True
                                    break
                
                if pattern_found:
                    break

# Also try specific known patterns
print("\n" + "=" * 60)
print("Testing specific EUR swap curve tickers...")

specific_tickers = [
    # Bloomberg standard curves
    "YCSW0045 Index",
    "YCGT0045 Index",
    
    # EUR swap vs EURIBOR
    "EUR1 Curncy",
    "EUR2 Curncy", 
    "EUR5 Curncy",
    "EUR10 Curncy",
    "EUR30 Curncy",
    
    # Alternative patterns
    "EURSW1 Curncy",
    "EURSW2 Curncy",
    "EURSW5 Curncy",
    "EURSW10 Curncy",
    
    # EUR benchmark yields
    "GTESP2Y Govt",
    "GTESP5Y Govt",
    "GTESP10Y Govt",
    "GTESP30Y Govt"
]

for ticker in specific_tickers:
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
        if "data" in data and "securities_data" in data["data"]:
            for sec_data in data["data"]["securities_data"]:
                if sec_data.get("fields", {}).get("PX_LAST") is not None:
                    rate = sec_data["fields"]["PX_LAST"]
                    name = sec_data["fields"].get("NAME", "")
                    crncy = sec_data["fields"].get("CRNCY", "")
                    print(f"✓ {ticker}: {rate:.4f} - {name} [{crncy}]")

print("\n" + "=" * 60)
print(f"Summary: Found {len(found_tickers)} potential long-end tickers")
if found_tickers:
    print("\nValid tickers by tenor:")
    for ticker, tenor, rate in sorted(found_tickers, key=lambda x: x[1]):
        print(f"  {tenor}Y: {ticker} = {rate:.4f}%")