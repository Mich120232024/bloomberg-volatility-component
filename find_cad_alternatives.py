#!/usr/bin/env python3
"""
Find CAD swap alternatives
"""

import requests

API_URL = "http://20.172.249.92:8080/api/bloomberg/reference"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer test"
}

# Try different CAD swap conventions
CAD_ALTERNATIVES = [
    # CORRA swaps (newer)
    "CCSO1 Curncy",
    "CCSO2 Curncy", 
    "CCSO3 Curncy",
    "CCSO5 Curncy",
    "CCSO7 Curncy",
    "CCSO10 Curncy",
    # CDOR basis swaps
    "CDOR1 Curncy",
    "CDOR2 Curncy",
    "CDOR5 Curncy",
    "CDOR10 Curncy",
    # Government bonds
    "GCAN2YR Index",
    "GCAN5YR Index", 
    "GCAN10YR Index",
    "GCAN30YR Index",
    # Alternative swap naming
    "CDSW1Y Curncy",
    "CDSW2Y Curncy",
    "CDSW5Y Curncy",
    "CDSW10Y Curncy"
]

print("CAD Alternative Tickers:")
print("-" * 60)

response = requests.post(
    API_URL,
    headers=HEADERS,
    json={"securities": CAD_ALTERNATIVES, "fields": ["PX_LAST", "YLD_YTM_MID", "SECURITY_DES"]},
    timeout=30
)

if response.status_code == 200:
    data = response.json()
    for i, sec_data in enumerate(data.get("data", {}).get("securities_data", [])):
        ticker = CAD_ALTERNATIVES[i]
        if sec_data.get("success"):
            px = sec_data.get("fields", {}).get("PX_LAST")
            yld = sec_data.get("fields", {}).get("YLD_YTM_MID")
            desc = sec_data.get("fields", {}).get("SECURITY_DES", "")
            value = px if px is not None else yld
            if value is not None:
                print(f"✓ {ticker:<20} {value:>8.3f}%  {desc[:30]}")
            else:
                print(f"✗ {ticker:<20} NO VALUE   {desc[:30]}")
        else:
            print(f"✗ {ticker:<20} INVALID")