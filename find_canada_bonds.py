#!/usr/bin/env python3
"""
Find Canadian government bond tickers
"""

import requests

API_URL = "http://20.172.249.92:8080/api/bloomberg/reference"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer test"
}

# Try Canadian government bonds
CANADA_BONDS = [
    # Generic government bond yields
    "GCAN1YR Index",
    "GCAN2YR Index",
    "GCAN3YR Index",
    "GCAN5YR Index",
    "GCAN7YR Index",
    "GCAN10YR Index",
    "GCAN30YR Index",
    # Alternative naming
    "CAN1Y Index",
    "CAN2Y Index",
    "CAN5Y Index",
    "CAN10Y Index",
    # Canadian Treasury bills
    "GCTB3M Index",
    "GCTB6M Index",
    "GCTB1Y Index",
    # CDOR-based swaps alternative
    "CDSWAP1 Curncy",
    "CDSWAP2 Curncy",
    "CDSWAP5 Curncy",
    "CDSWAP10 Curncy"
]

print("Canadian Government Bond Tickers:")
print("-" * 60)

response = requests.post(
    API_URL,
    headers=HEADERS,
    json={"securities": CANADA_BONDS, "fields": ["PX_LAST", "YLD_YTM_MID", "SECURITY_DES"]},
    timeout=30
)

if response.status_code == 200:
    data = response.json()
    for i, sec_data in enumerate(data.get("data", {}).get("securities_data", [])):
        ticker = CANADA_BONDS[i]
        if sec_data.get("success"):
            px = sec_data.get("fields", {}).get("PX_LAST")
            yld = sec_data.get("fields", {}).get("YLD_YTM_MID")
            desc = sec_data.get("fields", {}).get("SECURITY_DES", "")
            value = yld if yld is not None else px
            if value is not None:
                print(f"✓ {ticker:<20} {value:>8.3f}%  {desc[:35]}")
            else:
                print(f"✗ {ticker:<20} NO VALUE   {desc[:35]}")
        else:
            print(f"✗ {ticker:<20} INVALID")