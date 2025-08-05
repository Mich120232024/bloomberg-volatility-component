#!/usr/bin/env python3
"""
Check Bloomberg data availability for all yield curves
Verifies each currency's tickers one by one
"""

import requests
import json
from datetime import datetime

# Bloomberg API endpoint
API_URL = "http://20.172.249.92:8080/api/bloomberg/reference"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer test"
}

# Currency configurations from yieldCurveConfigs.ts
CURRENCIES = {
    "USD": {
        "name": "USD SOFR OIS",
        "tickers": [
            "SOFRRATE Index",
            "US0001M Index", "US0003M Index", "US0006M Index",
            "USSO1Z BGN Curncy", "USSO2Z BGN Curncy", "USSO3Z BGN Curncy",
            "USSOA BGN Curncy", "USSOB BGN Curncy", "USSOC BGN Curncy",
            "USSOD BGN Curncy", "USSOE BGN Curncy", "USSOF BGN Curncy",
            "USSOI BGN Curncy", "USSO1 BGN Curncy", "USSO1F BGN Curncy",
            "USGG2YR Index", "USGG5YR Index", "USGG10YR Index", "USGG30YR Index"
        ]
    },
    "EUR": {
        "name": "EUR ESTR OIS",
        "tickers": [
            "ESTR Index",
            "EUR001M Index", "EUR003M Index", "EUR006M Index",
            "EESWE1Z BGN Curncy", "EESWE2Z BGN Curncy", 
            "EESWEA BGN Curncy", "EESWEB BGN Curncy", "EESWEC BGN Curncy",
            "EESWED BGN Curncy", "EESWEE BGN Curncy", "EESWEF BGN Curncy",
            "EESWEG BGN Curncy", "EESWEH BGN Curncy", "EESWEI BGN Curncy",
            "EESWEJ BGN Curncy", "EESWEK BGN Curncy", "EESWE1 BGN Curncy",
            "EESWE1F BGN Curncy",
            "GDBR2 Index", "GDBR5 Index", "GDBR10 Index", "GDBR30 Index"
        ]
    },
    "GBP": {
        "name": "GBP SONIA OIS",
        "tickers": [
            "SONIO/N Index",
            "BP0001M Index", "BP0003M Index", "BP0006M Index",
            "BPSWS1Z BGN Curncy", "BPSWS2Z BGN Curncy",
            "BPSWSA BGN Curncy", "BPSWSB BGN Curncy", "BPSWSC BGN Curncy",
            "BPSWSD BGN Curncy", "BPSWSE BGN Curncy", "BPSWSF BGN Curncy",
            "BPSWSG BGN Curncy", "BPSWSH BGN Curncy", "BPSWSI BGN Curncy",
            "BPSWSJ BGN Curncy", "BPSWSK BGN Curncy", "BPSWS1 BGN Curncy",
            "BPSWS1F BGN Curncy", "BPSWS2 BGN Curncy", "BPSWS3 BGN Curncy",
            "BPSWS4 BGN Curncy", "BPSWS5 BGN Curncy", "BPSWS7 BGN Curncy",
            "BPSWS10 BGN Curncy", "BPSWS12 BGN Curncy", "BPSWS15 BGN Curncy",
            "BPSWS20 BGN Curncy", "BPSWS25 BGN Curncy", "BPSWS30 BGN Curncy"
        ]
    },
    "JPY": {
        "name": "JPY TONA OIS",
        "tickers": [
            "JYSO1Z BGN Curncy", "JYSO2Z BGN Curncy", "JYSO3Z BGN Curncy",
            "JYSOA BGN Curncy", "JYSOB BGN Curncy", "JYSOC BGN Curncy",
            "JYSOD BGN Curncy", "JYSOE BGN Curncy", "JYSOF BGN Curncy",
            "JYSOG BGN Curncy", "JYSOH BGN Curncy", "JYSOI BGN Curncy",
            "JYSOJ BGN Curncy", "JYSOK BGN Curncy", "JYSO1 BGN Curncy",
            "JYSO1C BGN Curncy", "JYSO1F BGN Curncy",
            "GJGB2 Index", "GJGB5 Index", "GJGB10 Index", "GJGB30 Index"
        ]
    },
    "CHF": {
        "name": "CHF SARON OIS",
        "tickers": [
            "SRFXON3 Index",
            "SF0001M Index", "SF0003M Index", "SF0006M Index",
            "SFSNT1Z BGNL Curncy", "SFSNT2Z BGNL Curncy",
            "SFSNTA BGNL Curncy", "SFSNTB BGNL Curncy", "SFSNTC BGNL Curncy",
            "SFSNTD BGNL Curncy", "SFSNTE BGNL Curncy", "SFSNTF BGNL Curncy",
            "SFSNTG BGNL Curncy", "SFSNTH BGNL Curncy", "SFSNTI BGNL Curncy",
            "SFSNTJ BGNL Curncy", "SFSNTK BGNL Curncy", "SFSNT1 BGNL Curncy",
            "SFSNT1C BGNL Curncy", "SFSNT1F BGNL Curncy", "SFSNT1I BGNL Curncy",
            "SFSNT2 BGNL Curncy", "SFSNT3 BGNL Curncy", "SFSNT4 BGNL Curncy",
            "SFSNT5 BGNL Curncy", "SFSNT6 BGNL Curncy", "SFSNT7 BGNL Curncy",
            "SFSNT8 BGNL Curncy", "SFSNT9 BGNL Curncy", "SFSNT10 BGNL Curncy",
            "SFSNT12 BGNL Curncy", "SFSNT15 BGNL Curncy", "SFSNT20 BGNL Curncy",
            "SFSNT25 BGNL Curncy", "SFSNT30 BGNL Curncy"
        ]
    },
    "AUD": {
        "name": "AUD BBSW IRS",
        "tickers": [
            "RBACOR Index",
            "ADBB1M Curncy", "ADBB3M Curncy", "ADBB6M Curncy",
            "ADSWAP1 Curncy", "ADSWAP2 Curncy", "ADSWAP3 Curncy",
            "ADSWAP4 Curncy", "ADSWAP5 Curncy", "ADSWAP7 Curncy",
            "ADSWAP10 Curncy", "ADSWAP15 Curncy", "ADSWAP20 Curncy",
            "ADSWAP30 Curncy"
        ]
    },
    "CAD": {
        "name": "CAD CDOR IRS",
        "tickers": [
            "CAONREPO Index",
            "CDOR01 Index", "CDOR03 Index", "CDOR06 Index",
            "CDSW1 Curncy", "CDSW2 Curncy", "CDSW3 Curncy",
            "CDSW4 Curncy", "CDSW5 Curncy", "CDSW7 Curncy",
            "CDSW10 Curncy", "CDSW15 Curncy", "CDSW20 Curncy",
            "CDSW30 Curncy"
        ]
    },
    "NZD": {
        "name": "NZD BKBM IRS",
        "tickers": [
            "NZOCR Index",
            "NDBK1M Index", "NDBK3M Index", "NDBK6M Index",
            "NDSWAP1 Curncy", "NDSWAP2 Curncy", "NDSWAP3 Curncy",
            "NDSWAP5 Curncy", "NDSWAP10 Curncy"
        ]
    },
    "SEK": {
        "name": "SEK STIBOR IRS",
        "tickers": [
            "STIBOR1M Index", "STIBOR3M Index", "STIBOR6M Index",
            "SKSW1 Curncy", "SKSW2 Curncy", "SKSW3 Curncy",
            "SKSW5 Curncy", "SKSW10 Curncy"
        ]
    },
    "NOK": {
        "name": "NOK NIBOR IRS", 
        "tickers": [
            "NIBOR1M Index", "NIBOR3M Index", "NIBOR6M Index",
            "NKSW1 Curncy", "NKSW2 Curncy", "NKSW3 Curncy",
            "NKSW5 Curncy", "NKSW10 Curncy"
        ]
    },
    "DKK": {
        "name": "DKK CIBOR IRS",
        "tickers": [
            "CIBOR1M Index", "CIBOR3M Index", "CIBOR6M Index",
            "EESWE1 BGN Curncy", "EESWE2 BGN Curncy", 
            "EESWE5 BGN Curncy", "EESWE10 BGN Curncy"
        ]
    },
    "ISK": {
        "name": "ISK REIBOR IRS",
        "tickers": [
            "REIB1M Index", "REIB3M Index", "REIB6M Index",
            "ISSO1 Curncy", "ISSO2 Curncy", "ISSO5 Curncy"
        ]
    }
}

def check_currency_tickers(currency: str, config: dict):
    """Check all tickers for a single currency"""
    print(f"\n{'='*60}")
    print(f"Checking {currency} - {config['name']}")
    print(f"{'='*60}")
    
    tickers = config['tickers']
    success_count = 0
    failed_tickers = []
    
    # Check in batches of 10
    batch_size = 10
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i+batch_size]
        
        try:
            response = requests.post(
                API_URL,
                headers=HEADERS,
                json={
                    "securities": batch,
                    "fields": ["PX_LAST", "YLD_YTM_MID", "DAYS_TO_MTY"]
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("data", {}).get("securities_data"):
                    for j, sec_data in enumerate(data["data"]["securities_data"]):
                        ticker = batch[j]
                        if sec_data.get("success"):
                            px_last = sec_data.get("fields", {}).get("PX_LAST")
                            yld = sec_data.get("fields", {}).get("YLD_YTM_MID")
                            value = px_last if px_last is not None else yld
                            
                            if value is not None:
                                print(f"  ✓ {ticker}: {value:.3f}")
                                success_count += 1
                            else:
                                print(f"  ✗ {ticker}: No data")
                                failed_tickers.append(ticker)
                        else:
                            error = sec_data.get("error", "Unknown error")
                            print(f"  ✗ {ticker}: {error}")
                            failed_tickers.append(ticker)
                else:
                    print(f"  ✗ Batch {i//batch_size + 1}: No data in response")
                    failed_tickers.extend(batch)
            else:
                print(f"  ✗ Batch {i//batch_size + 1}: HTTP {response.status_code}")
                failed_tickers.extend(batch)
                
        except Exception as e:
            print(f"  ✗ Batch {i//batch_size + 1}: {type(e).__name__}: {e}")
            failed_tickers.extend(batch)
    
    # Summary
    total = len(tickers)
    print(f"\nSummary for {currency}:")
    print(f"  Total tickers: {total}")
    print(f"  Success: {success_count} ({success_count/total*100:.1f}%)")
    print(f"  Failed: {len(failed_tickers)} ({len(failed_tickers)/total*100:.1f}%)")
    
    if failed_tickers:
        print(f"\nFailed tickers:")
        for ticker in failed_tickers[:5]:  # Show first 5
            print(f"    - {ticker}")
        if len(failed_tickers) > 5:
            print(f"    ... and {len(failed_tickers) - 5} more")
    
    return success_count, failed_tickers

def main():
    """Check all currencies"""
    print(f"Bloomberg Yield Curve Data Check")
    print(f"Started at: {datetime.now().isoformat()}")
    print(f"API: {API_URL}")
    
    overall_success = 0
    overall_failed = 0
    currency_results = {}
    
    # Check each currency
    for currency, config in CURRENCIES.items():
        success, failed = check_currency_tickers(currency, config)
        overall_success += success
        overall_failed += len(failed)
        currency_results[currency] = {
            "success": success,
            "failed": len(failed),
            "total": len(config["tickers"]),
            "rate": success / len(config["tickers"]) * 100
        }
    
    # Overall summary
    print(f"\n{'='*60}")
    print(f"OVERALL SUMMARY")
    print(f"{'='*60}")
    
    total_tickers = overall_success + overall_failed
    print(f"Total tickers checked: {total_tickers}")
    print(f"Overall success: {overall_success} ({overall_success/total_tickers*100:.1f}%)")
    print(f"Overall failed: {overall_failed} ({overall_failed/total_tickers*100:.1f}%)")
    
    print(f"\nPer Currency Success Rates:")
    for currency, results in sorted(currency_results.items(), key=lambda x: x[1]["rate"], reverse=True):
        print(f"  {currency:>3}: {results['rate']:>5.1f}% ({results['success']}/{results['total']})")
    
    print(f"\nCompleted at: {datetime.now().isoformat()}")

if __name__ == "__main__":
    main()