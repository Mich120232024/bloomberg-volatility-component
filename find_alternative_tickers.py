#!/usr/bin/env python3
"""
Find alternative tickers for problematic curves
"""

import requests

API_URL = "http://20.172.249.92:8080/api/bloomberg/reference"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer test"
}

# Alternative tickers to try
ALTERNATIVES = {
    "SEK Money Market": [
        "STIB1M Index",    # Try without OR
        "STIB3M Index",
        "STIB6M Index",
        "SKST1M Index",    # Alternative naming
        "SKST3M Index",
        "SKST6M Index",
        "SKSW1M Curncy",   # Swap rates
        "SKSW3M Curncy",
        "SKSW6M Curncy"
    ],
    "CAD Swaps": [
        "CDSWAP1 Curncy",  # Alternative naming
        "CDSWAP2 Curncy",
        "CDSWAP5 Curncy",
        "CDSWAP10 Curncy",
        "CDSW1 Index",     # Try as Index
        "CDSW2 Index",
        "CA0001Y Index",   # Canadian govt bonds
        "CA0002Y Index",
        "CA0005Y Index",
        "CA0010Y Index"
    ],
    "NZD Money Market": [
        "NZBK1M Index",    # Alternative naming
        "NZBK3M Index",
        "NZBK6M Index",
        "NDBM1M Index",
        "NDBM3M Index",
        "NDBM6M Index",
        "NZ0001M Index",
        "NZ0003M Index",
        "NZ0006M Index"
    ],
    "DKK Money Market": [
        "CIBO1M Index",    # Without R
        "CIBO3M Index",
        "CIBO6M Index",
        "DKCIBOR1M Index",
        "DKCIBOR3M Index",
        "DKCIBOR6M Index",
        "DK0001M Index",
        "DK0003M Index",
        "DK0006M Index"
    ]
}

for category, tickers in ALTERNATIVES.items():
    print(f"\n{category} - Checking alternatives:")
    print("-" * 50)
    
    response = requests.post(
        API_URL,
        headers=HEADERS,
        json={"securities": tickers, "fields": ["PX_LAST", "SECURITY_DES"]},
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        for i, sec_data in enumerate(data.get("data", {}).get("securities_data", [])):
            ticker = tickers[i]
            if sec_data.get("success"):
                value = sec_data.get("fields", {}).get("PX_LAST")
                desc = sec_data.get("fields", {}).get("SECURITY_DES", "")
                if value is not None:
                    print(f"✓ {ticker:<20} {value:>8.3f}%  {desc}")
                else:
                    print(f"✗ {ticker:<20} NO VALUE   {desc}")
            else:
                print(f"✗ {ticker:<20} INVALID")