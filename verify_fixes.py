#!/usr/bin/env python3
"""
Verify all the ticker fixes work
"""

import requests

API_URL = "http://20.172.249.92:8080/api/bloomberg/reference"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer test"
}

# Fixed tickers to verify
FIXED_CURVES = {
    "SEK": [
        "STIB1M Index",    # Fixed from STIBOR1M
        "STIB3M Index", 
        "STIB6M Index",
        "SKSW1 Curncy",
        "SKSW5 Curncy"
    ],
    "CAD": [
        "CAONREPO Index",
        "CDOR01 Index",
        "CCSO1 Curncy",    # Fixed from CDSW1
        "CCSO2 Curncy",
        "CCSO3 Curncy",
        "CCSO5 Curncy"
    ],
    "NZD": [
        "NZOCR Index",
        "NZ0001M Index",   # Fixed from NDBK1M
        "NZ0003M Index",
        "NZ0006M Index",
        "NDSWAP1 Curncy",
        "NDSWAP5 Curncy"
    ],
    "DKK": [
        "DK0001M Index",   # Fixed from CIBOR1M
        "DK0003M Index",
        "DK0006M Index",
        "EESWE1 BGN Curncy",
        "EESWE5 BGN Curncy"
    ],
    "ISK": [
        "IKSW1 Curncy",    # Fixed from ISSO1
        "IKSW2 Curncy",
        "IKSW5 Curncy"
    ]
}

for currency, tickers in FIXED_CURVES.items():
    print(f"\n{currency} Fixed Tickers Verification:")
    print("-" * 50)
    
    response = requests.post(
        API_URL,
        headers=HEADERS,
        json={"securities": tickers, "fields": ["PX_LAST", "YLD_YTM_MID"]},
        timeout=30
    )
    
    success_count = 0
    if response.status_code == 200:
        data = response.json()
        for i, sec_data in enumerate(data.get("data", {}).get("securities_data", [])):
            ticker = tickers[i]
            if sec_data.get("success"):
                value = sec_data.get("fields", {}).get("PX_LAST") or sec_data.get("fields", {}).get("YLD_YTM_MID")
                if value is not None:
                    print(f"  ✓ {ticker:<20} {value:>8.3f}%")
                    success_count += 1
                else:
                    print(f"  ✗ {ticker:<20} NO DATA")
            else:
                print(f"  ✗ {ticker:<20} ERROR")
    
    print(f"  Success rate: {success_count}/{len(tickers)} ({success_count/len(tickers)*100:.0f}%)")