#!/usr/bin/env python3
"""
Find yield curve tickers for more EM currencies
"""

import requests

API_URL = "http://20.172.249.92:8080/api/bloomberg/reference"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer test"
}

# More EM currencies
EM_CURRENCIES = {
    "SGD": [
        # Money market
        "SIBOR1M Index", "SIBOR3M Index", "SIBOR6M Index",
        # Swaps
        "SDSW1 Curncy", "SDSW2 Curncy", "SDSW3 Curncy",
        "SDSW5 Curncy", "SDSW10 Curncy",
        # Government bonds
        "MASB2Y Index", "MASB5Y Index", "MASB10Y Index"
    ],
    "INR": [
        # Money market
        "INRFBIL Index", "MIBOR1M Index", "MIBOR3M Index",
        # Swaps
        "INSW1 Curncy", "INSW2 Curncy", "INSW3 Curncy",
        "INSW5 Curncy", "INSW10 Curncy",
        # OIS
        "INSO1 Curncy", "INSO2 Curncy", "INSO5 Curncy",
        # Government bonds
        "GIND2YR Index", "GIND5YR Index", "GIND10YR Index"
    ],
    "THB": [
        # Money market
        "TBDC1M Index", "TBDC3M Index", "TBDC6M Index",
        # Swaps
        "THSW1 Curncy", "THSW2 Curncy", "THSW3 Curncy",
        "THSW5 Curncy", "THSW10 Curncy",
        # Government bonds
        "GVTL2Y Index", "GVTL5Y Index", "GVTL10Y Index"
    ],
    "TRY": [
        # Money market
        "TRLIB1M Index", "TRLIB3M Index", "TRLIB6M Index",
        # Swaps
        "TYSW1 Curncy", "TYSW2 Curncy", "TYSW3 Curncy",
        "TYSW5 Curncy", "TYSW10 Curncy",
        # Government bonds
        "IECM2Y Index", "IECM5Y Index", "IECM10Y Index"
    ],
    "PLN": [
        # Money market
        "WIBO1M Index", "WIBO3M Index", "WIBO6M Index",
        # Swaps
        "PZSW1 Curncy", "PZSW2 Curncy", "PZSW3 Curncy",
        "PZSW5 Curncy", "PZSW10 Curncy",
        # Government bonds
        "POLGB2Y Index", "POLGB5Y Index", "POLGB10Y Index"
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