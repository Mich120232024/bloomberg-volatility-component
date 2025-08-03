#!/usr/bin/env python3
"""
Find yield curve tickers for remaining EM currencies
"""

import requests

API_URL = "http://20.172.249.92:8080/api/bloomberg/reference"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer test"
}

# Remaining EM currencies
EM_CURRENCIES = {
    "HUF": [
        # Money market
        "BUBOR1M Index", "BUBOR3M Index", "BUBOR6M Index",
        # Swaps
        "HFSW1 Curncy", "HFSW2 Curncy", "HFSW3 Curncy",
        "HFSW5 Curncy", "HFSW10 Curncy",
        # Government bonds
        "GHGB2Y Index", "GHGB5Y Index", "GHGB10Y Index"
    ],
    "CZK": [
        # Money market
        "PRIB01M Index", "PRIB03M Index", "PRIB06M Index",
        # Swaps
        "CKSW1 Curncy", "CKSW2 Curncy", "CKSW3 Curncy",
        "CKSW5 Curncy", "CKSW10 Curncy",
        # Government bonds
        "CZGB2Y Index", "CZGB5Y Index", "CZGB10Y Index"
    ],
    "ILS": [
        # Money market
        "TELBOR1M Index", "TELBOR3M Index", "TELBOR6M Index",
        # Swaps
        "ISSW1 Curncy", "ISSW2 Curncy", "ISSW3 Curncy",
        "ISSW5 Curncy", "ISSW10 Curncy",
        # Government bonds
        "ILGV2Y Index", "ILGV5Y Index", "ILGV10Y Index"
    ],
    "RUB": [
        # Money market
        "MOSPRIME1M Index", "MOSPRIME3M Index", "MOSPRIME6M Index",
        # Swaps
        "RRSW1 Curncy", "RRSW2 Curncy", "RRSW3 Curncy",
        "RRSW5 Curncy", "RRSW10 Curncy",
        # Government bonds
        "RUGE2Y Index", "RUGE5Y Index", "RUGE10Y Index"
    ],
    "TWD": [
        # Money market
        "TAIBOR1M Index", "TAIBOR3M Index", "TAIBOR6M Index",
        # Swaps
        "NTSW1 Curncy", "NTSW2 Curncy", "NTSW3 Curncy",
        "NTSW5 Curncy", "NTSW10 Curncy",
        # Government bonds
        "GVTW2Y Index", "GVTW5Y Index", "GVTW10Y Index"
    ],
    "PHP": [
        # Government bonds only
        "PDSF2Y Index", "PDSF5Y Index", "PDSF10Y Index",
        # Treasury bills
        "PDST3M Index", "PDST6M Index", "PDST1Y Index"
    ],
    "HKD": [
        # Money market
        "HIBOR1M Index", "HIBOR3M Index", "HIBOR6M Index",
        # Swaps
        "HDSW1 Curncy", "HDSW2 Curncy", "HDSW3 Curncy",
        "HDSW5 Curncy", "HDSW10 Curncy",
        # Government bonds
        "HKGG2Y Index", "HKGG5Y Index", "HKGG10Y Index"
    ]
}

for currency, tickers in EM_CURRENCIES.items():
    print(f"\n{currency} Yield Curve Tickers:")
    print("-" * 60)
    
    # Check in batches
    for i in range(0, len(tickers), 5):
        batch = tickers[i:i+5]
        response = requests.post(
            API_URL,
            headers=HEADERS,
            json={"securities": batch, "fields": ["PX_LAST", "YLD_YTM_MID", "SECURITY_DES"]},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            for j, sec_data in enumerate(data.get("data", {}).get("securities_data", [])):
                ticker = batch[j]
                if sec_data.get("success"):
                    px = sec_data.get("fields", {}).get("PX_LAST")
                    yld = sec_data.get("fields", {}).get("YLD_YTM_MID")
                    desc = sec_data.get("fields", {}).get("SECURITY_DES", "")[:30]
                    value = yld if yld is not None else px
                    if value is not None:
                        print(f"  ✓ {ticker:<25} {value:>8.3f}%  {desc}")
                    else:
                        print(f"  ✗ {ticker:<25} NO VALUE   {desc}")
                else:
                    print(f"  ✗ {ticker:<25} INVALID")