#!/usr/bin/env python3
"""
Find ISK alternatives
"""

import requests

API_URL = "http://20.172.249.92:8080/api/bloomberg/reference"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer test"
}

# Try different ISK alternatives
ISK_ALTERNATIVES = [
    # Government bonds
    "GICE2YR Index",
    "GICE5YR Index",
    "GICE10YR Index",
    # Alternative naming
    "ICEIBOR1M Index",
    "ICEIBOR3M Index",
    "ICEIBOR6M Index",
    # REIBOR without space
    "REIBOR1M Index",
    "REIBOR3M Index",
    "REIBOR6M Index",
    # Generic Iceland rates
    "IS0001M Index",
    "IS0003M Index",
    "IS0006M Index",
    # ISK swaps alternative naming
    "IKSW1 Curncy",
    "IKSW2 Curncy",
    "IKSW5 Curncy",
    # Iceland Central Bank rate
    "SEDLABAN Index",
    "ICECBDR Index"
]

print("ISK Alternative Tickers:")
print("-" * 60)

response = requests.post(
    API_URL,
    headers=HEADERS,
    json={"securities": ISK_ALTERNATIVES, "fields": ["PX_LAST", "YLD_YTM_MID", "SECURITY_DES"]},
    timeout=30
)

if response.status_code == 200:
    data = response.json()
    for i, sec_data in enumerate(data.get("data", {}).get("securities_data", [])):
        ticker = ISK_ALTERNATIVES[i]
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