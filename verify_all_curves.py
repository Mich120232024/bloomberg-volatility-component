#!/usr/bin/env python3
"""
Verify all yield curves in the coverage universe
"""

import requests
from datetime import datetime

API_URL = "http://20.172.249.92:8080/api/bloomberg/reference"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer test"
}

# All currencies in our universe
ALL_CURRENCIES = [
    # G10
    "USD", "EUR", "GBP", "JPY", "CHF", "AUD", "CAD", "NOK", "SEK", "NZD",
    # European
    "DKK", "ISK", "PLN", "CZK", "HUF",
    # EM - Asia
    "CNH", "KRW", "SGD", "THB", "TWD", "INR", "PHP", "HKD",
    # EM - Others
    "MXN", "TRY", "ZAR", "RUB", "BRL", "ILS"
]

# Key tickers to check for each currency
KEY_TICKERS = {
    "USD": ["SOFRRATE Index", "USSO1 BGN Curncy", "USGG10YR Index"],
    "EUR": ["ESTR Index", "EESWE1 BGN Curncy", "GDBR10 Index"],
    "GBP": ["SONIO/N Index", "BPSWS1 BGN Curncy", "BPSWS10 BGN Curncy"],
    "JPY": ["JYSO1 BGN Curncy", "GJGB10 Index"],
    "CHF": ["SRFXON3 Index", "SFSNT1 BGNL Curncy", "SFSNT10 BGNL Curncy"],
    "AUD": ["RBACOR Index", "ADSWAP1 Curncy", "ADSWAP10 Curncy"],
    "CAD": ["CAONREPO Index", "GCAN10YR Index"],
    "NOK": ["NIBOR3M Index", "NKSW5 Curncy"],
    "SEK": ["STIB3M Index", "SKSW5 Curncy"],
    "NZD": ["NZOCR Index", "NDSWAP5 Curncy"],
    "DKK": ["DK0003M Index", "EESWE5 BGN Curncy"],
    "ISK": ["IKSW5 Curncy"],
    "PLN": ["WIBO3M Index", "PZSW5 Curncy"],
    "CZK": ["PRIB03M Index", "CKSW5 Curncy"],
    "HUF": ["HFSW5 Curncy", "GHGB10Y Index"],
    "CNH": ["GCNY5Y Index"],
    "KRW": ["GVSK5Y Index"],
    "SGD": ["MASB5Y Index"],
    "THB": ["TBDC3M Index", "GVTL5Y Index"],
    "TWD": ["TAIBOR3M Index"],
    "INR": ["GIND5YR Index"],
    "PHP": ["PDSF5Y Index"],
    "HKD": ["HDSW5 Curncy", "HKGG5Y Index"],
    "MXN": ["GMXN05YR Index"],
    "TRY": ["TRLIB3M Index", "IECM5Y Index"],
    "ZAR": ["JIBA3M Index", "SASW5 Curncy"],
    "RUB": ["RUGE10Y Index"],
    "BRL": [],  # No working tickers
    "ILS": []   # No working tickers
}

print(f"Coverage Universe Yield Curve Verification")
print(f"Started: {datetime.now().isoformat()}")
print(f"{'='*70}\n")

summary = {
    "full_coverage": [],
    "partial_coverage": [],
    "no_coverage": []
}

for currency in ALL_CURRENCIES:
    tickers = KEY_TICKERS.get(currency, [])
    
    if not tickers:
        print(f"{currency}: ❌ No tickers configured")
        summary["no_coverage"].append(currency)
        continue
    
    # Check tickers
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
            if sec_data.get("success"):
                value = sec_data.get("fields", {}).get("PX_LAST") or sec_data.get("fields", {}).get("YLD_YTM_MID")
                if value is not None:
                    success_count += 1
    
    if success_count == len(tickers):
        print(f"{currency}: ✅ Full coverage ({success_count}/{len(tickers)} tickers)")
        summary["full_coverage"].append(currency)
    elif success_count > 0:
        print(f"{currency}: ⚠️  Partial coverage ({success_count}/{len(tickers)} tickers)")
        summary["partial_coverage"].append(currency)
    else:
        print(f"{currency}: ❌ No data")
        summary["no_coverage"].append(currency)

print(f"\n{'='*70}")
print("SUMMARY")
print(f"{'='*70}")
print(f"✅ Full Coverage ({len(summary['full_coverage'])}): {', '.join(summary['full_coverage'])}")
print(f"⚠️  Partial Coverage ({len(summary['partial_coverage'])}): {', '.join(summary['partial_coverage'])}")
print(f"❌ No Coverage ({len(summary['no_coverage'])}): {', '.join(summary['no_coverage'])}")
print(f"\nTotal: {len(ALL_CURRENCIES)} currencies")
print(f"Coverage Rate: {(len(summary['full_coverage']) + len(summary['partial_coverage'])) / len(ALL_CURRENCIES) * 100:.1f}%")