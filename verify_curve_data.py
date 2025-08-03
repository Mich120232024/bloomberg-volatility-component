#!/usr/bin/env python3
"""
Verify specific curve data points for visual inspection
"""

import requests
import json

API_URL = "http://20.172.249.92:8080/api/bloomberg/reference"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer test"
}

# Focus on problematic curves
CURVES = {
    "SEK": [
        "STIBOR1M Index", "STIBOR3M Index", "STIBOR6M Index",
        "SKSW1 Curncy", "SKSW2 Curncy", "SKSW3 Curncy",
        "SKSW5 Curncy", "SKSW10 Curncy"
    ],
    "CAD": [
        "CAONREPO Index", "CDOR01 Index", "CDOR03 Index", "CDOR06 Index",
        "CDSW1 Curncy", "CDSW2 Curncy", "CDSW5 Curncy", "CDSW10 Curncy"
    ],
    "CHF": [
        "SRFXON3 Index", "SF0001M Index", "SF0003M Index",
        "SFSNT1 BGNL Curncy", "SFSNT2 BGNL Curncy", "SFSNT5 BGNL Curncy"
    ],
    "NZD": [
        "NZOCR Index", "NDBK1M Index", "NDBK3M Index",
        "NDSWAP1 Curncy", "NDSWAP2 Curncy", "NDSWAP5 Curncy", "NDSWAP10 Curncy"
    ]
}

for currency, tickers in CURVES.items():
    print(f"\n{currency} Curve Data:")
    print("-" * 40)
    
    response = requests.post(
        API_URL,
        headers=HEADERS,
        json={"securities": tickers, "fields": ["PX_LAST", "YLD_YTM_MID"]},
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        for i, sec_data in enumerate(data.get("data", {}).get("securities_data", [])):
            ticker = tickers[i]
            if sec_data.get("success"):
                value = sec_data.get("fields", {}).get("PX_LAST") or sec_data.get("fields", {}).get("YLD_YTM_MID")
                print(f"  {ticker:<20} {value:>8.3f}%" if value else f"  {ticker:<20} NO DATA")
            else:
                print(f"  {ticker:<20} ERROR: {sec_data.get('error', 'Unknown')}")