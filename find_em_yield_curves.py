#!/usr/bin/env python3
"""
Find yield curve tickers for EM currencies
"""

import requests

API_URL = "http://20.172.249.92:8080/api/bloomberg/reference"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer test"
}

# EM currencies to check
EM_CURRENCIES = {
    "BRL": [
        # Money market
        "BZDI1M Index", "BZ0001M Index", "BRL1M Index",
        # Swaps
        "BRSWP1 ICPL Curncy", "BRSWP2 ICPL Curncy", "BRSWP3 ICPL Curncy",
        "BRSWP5 ICPL Curncy", "BRSWP10 ICPL Curncy",
        # Alternative swaps
        "BZSW1 Curncy", "BZSW2 Curncy", "BZSW5 Curncy", "BZSW10 Curncy",
        # Government bonds
        "BZGV2Y Index", "BZGV5Y Index", "BZGV10Y Index"
    ],
    "CNH": [
        # Money market
        "CNDR1W Curncy", "CNDR1M Curncy", "CNDR3M Curncy",
        # Swaps
        "CCSW1 CNCC Curncy", "CCSW2 CNCC Curncy", "CCSW3 CNCC Curncy",
        "CCSW5 CNCC Curncy", "CCSW10 CNCC Curncy",
        # Alternative
        "CHSW1 Curncy", "CHSW2 Curncy", "CHSW5 Curncy",
        # Government bonds
        "GCNY2Y Index", "GCNY5Y Index", "GCNY10Y Index"
    ],
    "KRW": [
        # Money market
        "KWCD1M Index", "KWCD3M Index", "KWCD6M Index",
        # Swaps
        "KWSW1 Curncy", "KWSW2 Curncy", "KWSW3 Curncy",
        "KWSW5 Curncy", "KWSW10 Curncy",
        # Government bonds
        "GVSK2Y Index", "GVSK5Y Index", "GVSK10Y Index"
    ],
    "MXN": [
        # Money market
        "MXIBTIIE Index", "MPRATE28 Index", "MPRATE91 Index",
        # Swaps
        "MPSW1 Curncy", "MPSW2 Curncy", "MPSW3 Curncy",
        "MPSW5 Curncy", "MPSW10 Curncy",
        # Government bonds
        "GMXN02YR Index", "GMXN05YR Index", "GMXN10YR Index"
    ],
    "ZAR": [
        # Money market
        "JIBA1M Index", "JIBA3M Index", "JIBA6M Index",
        # Swaps
        "SASW1 Curncy", "SASW2 Curncy", "SASW3 Curncy",
        "SASW5 Curncy", "SASW10 Curncy",
        # Government bonds
        "GSAB2Y Index", "GSAB5Y Index", "GSAB10Y Index"
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