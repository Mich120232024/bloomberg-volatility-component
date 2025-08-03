#!/usr/bin/env python3
import requests
import time

bloomberg_url = "http://20.172.249.92:8080"

# Complete ticker lists for each currency based on discovery
g10_curves = {
    'JPY': {
        'overnight': 'MUTKCALM Index',
        'tickers': [
            {'ticker': 'MUTKCALM Index', 'tenor': 'O/N', 'tenor_numeric': 1},
            # Monthly swaps
            {'ticker': 'JYSOA Curncy', 'tenor': '1M', 'tenor_numeric': 30},
            {'ticker': 'JYSOB Curncy', 'tenor': '2M', 'tenor_numeric': 60},
            {'ticker': 'JYSOC Curncy', 'tenor': '3M', 'tenor_numeric': 90},
            {'ticker': 'JYSOD Curncy', 'tenor': '4M', 'tenor_numeric': 120},
            {'ticker': 'JYSOE Curncy', 'tenor': '5M', 'tenor_numeric': 150},
            {'ticker': 'JYSOF Curncy', 'tenor': '6M', 'tenor_numeric': 180},
            {'ticker': 'JYSOG Curncy', 'tenor': '7M', 'tenor_numeric': 210},
            {'ticker': 'JYSOH Curncy', 'tenor': '8M', 'tenor_numeric': 240},
            {'ticker': 'JYSOI Curncy', 'tenor': '9M', 'tenor_numeric': 270},
            {'ticker': 'JYSOJ Curncy', 'tenor': '10M', 'tenor_numeric': 300},
            {'ticker': 'JYSOK Curncy', 'tenor': '11M', 'tenor_numeric': 330},
            # Yearly swaps
            {'ticker': 'JYSO1 Curncy', 'tenor': '1Y', 'tenor_numeric': 1},
            {'ticker': 'JYSO2 Curncy', 'tenor': '2Y', 'tenor_numeric': 2},
            {'ticker': 'JYSO3 Curncy', 'tenor': '3Y', 'tenor_numeric': 3},
            {'ticker': 'JYSO4 Curncy', 'tenor': '4Y', 'tenor_numeric': 4},
            {'ticker': 'JYSO5 Curncy', 'tenor': '5Y', 'tenor_numeric': 5},
            {'ticker': 'JYSO7 Curncy', 'tenor': '7Y', 'tenor_numeric': 7},
            {'ticker': 'JYSO10 Curncy', 'tenor': '10Y', 'tenor_numeric': 10},
            {'ticker': 'JYSO15 Curncy', 'tenor': '15Y', 'tenor_numeric': 15},
            {'ticker': 'JYSO20 Curncy', 'tenor': '20Y', 'tenor_numeric': 20},
            {'ticker': 'JYSO30 Curncy', 'tenor': '30Y', 'tenor_numeric': 30},
        ]
    },
    'CAD': {
        'overnight': 'CAONREPO Index',
        'tickers': [
            {'ticker': 'CAONREPO Index', 'tenor': 'O/N', 'tenor_numeric': 1},
            # Monthly swaps
            {'ticker': 'CDSOA Curncy', 'tenor': '1M', 'tenor_numeric': 30},
            {'ticker': 'CDSOB Curncy', 'tenor': '2M', 'tenor_numeric': 60},
            {'ticker': 'CDSOC Curncy', 'tenor': '3M', 'tenor_numeric': 90},
            {'ticker': 'CDSOD Curncy', 'tenor': '4M', 'tenor_numeric': 120},
            {'ticker': 'CDSOE Curncy', 'tenor': '5M', 'tenor_numeric': 150},
            {'ticker': 'CDSOF Curncy', 'tenor': '6M', 'tenor_numeric': 180},
            {'ticker': 'CDSOG Curncy', 'tenor': '7M', 'tenor_numeric': 210},
            {'ticker': 'CDSOH Curncy', 'tenor': '8M', 'tenor_numeric': 240},
            {'ticker': 'CDSOI Curncy', 'tenor': '9M', 'tenor_numeric': 270},
            {'ticker': 'CDSOJ Curncy', 'tenor': '10M', 'tenor_numeric': 300},
            {'ticker': 'CDSOK Curncy', 'tenor': '11M', 'tenor_numeric': 330},
            # Yearly swaps
            {'ticker': 'CDSO1 Curncy', 'tenor': '1Y', 'tenor_numeric': 1},
            {'ticker': 'CDSO2 Curncy', 'tenor': '2Y', 'tenor_numeric': 2},
            {'ticker': 'CDSO3 Curncy', 'tenor': '3Y', 'tenor_numeric': 3},
            {'ticker': 'CDSO4 Curncy', 'tenor': '4Y', 'tenor_numeric': 4},
            {'ticker': 'CDSO5 Curncy', 'tenor': '5Y', 'tenor_numeric': 5},
            {'ticker': 'CDSO7 Curncy', 'tenor': '7Y', 'tenor_numeric': 7},
            {'ticker': 'CDSO10 Curncy', 'tenor': '10Y', 'tenor_numeric': 10},
            {'ticker': 'CDSO15 Curncy', 'tenor': '15Y', 'tenor_numeric': 15},
            {'ticker': 'CDSO20 Curncy', 'tenor': '20Y', 'tenor_numeric': 20},
            {'ticker': 'CDSO30 Curncy', 'tenor': '30Y', 'tenor_numeric': 30},
        ]
    },
    'AUD': {
        'overnight': 'RBACOR Index',
        'tickers': [
            {'ticker': 'RBACOR Index', 'tenor': 'O/N', 'tenor_numeric': 1},
            # Monthly swaps
            {'ticker': 'ADSOA Curncy', 'tenor': '1M', 'tenor_numeric': 30},
            {'ticker': 'ADSOB Curncy', 'tenor': '2M', 'tenor_numeric': 60},
            {'ticker': 'ADSOC Curncy', 'tenor': '3M', 'tenor_numeric': 90},
            {'ticker': 'ADSOD Curncy', 'tenor': '4M', 'tenor_numeric': 120},
            {'ticker': 'ADSOE Curncy', 'tenor': '5M', 'tenor_numeric': 150},
            {'ticker': 'ADSOF Curncy', 'tenor': '6M', 'tenor_numeric': 180},
            {'ticker': 'ADSOG Curncy', 'tenor': '7M', 'tenor_numeric': 210},
            {'ticker': 'ADSOH Curncy', 'tenor': '8M', 'tenor_numeric': 240},
            {'ticker': 'ADSOI Curncy', 'tenor': '9M', 'tenor_numeric': 270},
            {'ticker': 'ADSOJ Curncy', 'tenor': '10M', 'tenor_numeric': 300},
            {'ticker': 'ADSOK Curncy', 'tenor': '11M', 'tenor_numeric': 330},
            # Yearly swaps
            {'ticker': 'ADSO1 Curncy', 'tenor': '1Y', 'tenor_numeric': 1},
            {'ticker': 'ADSO2 Curncy', 'tenor': '2Y', 'tenor_numeric': 2},
            {'ticker': 'ADSO3 Curncy', 'tenor': '3Y', 'tenor_numeric': 3},
            {'ticker': 'ADSO4 Curncy', 'tenor': '4Y', 'tenor_numeric': 4},
            {'ticker': 'ADSO5 Curncy', 'tenor': '5Y', 'tenor_numeric': 5},
            {'ticker': 'ADSO7 Curncy', 'tenor': '7Y', 'tenor_numeric': 7},
            {'ticker': 'ADSO10 Curncy', 'tenor': '10Y', 'tenor_numeric': 10},
            {'ticker': 'ADSO15 Curncy', 'tenor': '15Y', 'tenor_numeric': 15},
            {'ticker': 'ADSO20 Curncy', 'tenor': '20Y', 'tenor_numeric': 20},
            {'ticker': 'ADSO30 Curncy', 'tenor': '30Y', 'tenor_numeric': 30},
        ]
    },
    'NZD': {
        'overnight': 'NZOCRS Index',
        'tickers': [
            {'ticker': 'NZOCRS Index', 'tenor': 'O/N', 'tenor_numeric': 1},
            # Monthly swaps
            {'ticker': 'NDSOA Curncy', 'tenor': '1M', 'tenor_numeric': 30},
            {'ticker': 'NDSOB Curncy', 'tenor': '2M', 'tenor_numeric': 60},
            {'ticker': 'NDSOC Curncy', 'tenor': '3M', 'tenor_numeric': 90},
            {'ticker': 'NDSOD Curncy', 'tenor': '4M', 'tenor_numeric': 120},
            {'ticker': 'NDSOE Curncy', 'tenor': '5M', 'tenor_numeric': 150},
            {'ticker': 'NDSOF Curncy', 'tenor': '6M', 'tenor_numeric': 180},
            {'ticker': 'NDSOG Curncy', 'tenor': '7M', 'tenor_numeric': 210},
            {'ticker': 'NDSOH Curncy', 'tenor': '8M', 'tenor_numeric': 240},
            {'ticker': 'NDSOI Curncy', 'tenor': '9M', 'tenor_numeric': 270},
            {'ticker': 'NDSOJ Curncy', 'tenor': '10M', 'tenor_numeric': 300},
            {'ticker': 'NDSOK Curncy', 'tenor': '11M', 'tenor_numeric': 330},
            # Yearly swaps
            {'ticker': 'NDSO1 Curncy', 'tenor': '1Y', 'tenor_numeric': 1},
            {'ticker': 'NDSO2 Curncy', 'tenor': '2Y', 'tenor_numeric': 2},
            {'ticker': 'NDSO3 Curncy', 'tenor': '3Y', 'tenor_numeric': 3},
            {'ticker': 'NDSO4 Curncy', 'tenor': '4Y', 'tenor_numeric': 4},
            {'ticker': 'NDSO5 Curncy', 'tenor': '5Y', 'tenor_numeric': 5},
            {'ticker': 'NDSO7 Curncy', 'tenor': '7Y', 'tenor_numeric': 7},
            {'ticker': 'NDSO10 Curncy', 'tenor': '10Y', 'tenor_numeric': 10},
            {'ticker': 'NDSO15 Curncy', 'tenor': '15Y', 'tenor_numeric': 15},
            {'ticker': 'NDSO20 Curncy', 'tenor': '20Y', 'tenor_numeric': 20},
            {'ticker': 'NDSO30 Curncy', 'tenor': '30Y', 'tenor_numeric': 30},
        ]
    },
    'SEK': {
        'overnight': 'STIB1W Index',  # Using 1W as proxy for overnight
        'tickers': [
            {'ticker': 'STIB1W Index', 'tenor': '1W', 'tenor_numeric': 7},
            # IRS swaps vs 3M STIBOR
            {'ticker': 'SKSW1 Curncy', 'tenor': '1Y', 'tenor_numeric': 1},
            {'ticker': 'SKSW2 Curncy', 'tenor': '2Y', 'tenor_numeric': 2},
            {'ticker': 'SKSW3 Curncy', 'tenor': '3Y', 'tenor_numeric': 3},
            {'ticker': 'SKSW4 Curncy', 'tenor': '4Y', 'tenor_numeric': 4},
            {'ticker': 'SKSW5 Curncy', 'tenor': '5Y', 'tenor_numeric': 5},
            {'ticker': 'SKSW7 Curncy', 'tenor': '7Y', 'tenor_numeric': 7},
            {'ticker': 'SKSW10 Curncy', 'tenor': '10Y', 'tenor_numeric': 10},
            {'ticker': 'SKSW15 Curncy', 'tenor': '15Y', 'tenor_numeric': 15},
            {'ticker': 'SKSW20 Curncy', 'tenor': '20Y', 'tenor_numeric': 20},
            {'ticker': 'SKSW30 Curncy', 'tenor': '30Y', 'tenor_numeric': 30},
        ]
    },
    'NOK': {
        'overnight': 'NIBOR1W Index',  # Using 1W as proxy for overnight
        'tickers': [
            {'ticker': 'NIBOR1W Index', 'tenor': '1W', 'tenor_numeric': 7},
            # IRS swaps vs 6M NIBOR
            {'ticker': 'NKSW1 Curncy', 'tenor': '1Y', 'tenor_numeric': 1},
            {'ticker': 'NKSW2 Curncy', 'tenor': '2Y', 'tenor_numeric': 2},
            {'ticker': 'NKSW3 Curncy', 'tenor': '3Y', 'tenor_numeric': 3},
            {'ticker': 'NKSW4 Curncy', 'tenor': '4Y', 'tenor_numeric': 4},
            {'ticker': 'NKSW5 Curncy', 'tenor': '5Y', 'tenor_numeric': 5},
            {'ticker': 'NKSW7 Curncy', 'tenor': '7Y', 'tenor_numeric': 7},
            {'ticker': 'NKSW10 Curncy', 'tenor': '10Y', 'tenor_numeric': 10},
            {'ticker': 'NKSW15 Curncy', 'tenor': '15Y', 'tenor_numeric': 15},
            {'ticker': 'NKSW20 Curncy', 'tenor': '20Y', 'tenor_numeric': 20},
            {'ticker': 'NKSW30 Curncy', 'tenor': '30Y', 'tenor_numeric': 30},
        ]
    }
}

# Validate all tickers
for currency, config in g10_curves.items():
    print(f"\n{'='*60}")
    print(f"Validating {currency} curve...")
    print(f"{'='*60}")
    
    valid_count = 0
    ticker_list = []
    
    for ticker_info in config['tickers']:
        ticker = ticker_info['ticker']
        try:
            response = requests.post(
                f"{bloomberg_url}/api/bloomberg/reference",
                headers={"Authorization": "Bearer test"},
                json={
                    "securities": [ticker],
                    "fields": ["PX_LAST", "NAME"]
                },
                timeout=3
            )
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and "securities_data" in data["data"]:
                    for sec_data in data["data"]["securities_data"]:
                        if sec_data.get("success"):
                            rate = sec_data["fields"].get("PX_LAST")
                            name = sec_data["fields"].get("NAME", "")
                            
                            if rate is not None:
                                print(f"✓ {ticker} ({ticker_info['tenor']}): {rate:.4f}% - {name}")
                                valid_count += 1
                                ticker_list.append(ticker)
                            else:
                                print(f"✗ {ticker} ({ticker_info['tenor']}): No rate data")
                        else:
                            print(f"✗ {ticker} ({ticker_info['tenor']}): Failed")
        except Exception as e:
            print(f"✗ {ticker} ({ticker_info['tenor']}): Error - {e}")
        
        time.sleep(0.1)  # Rate limiting
    
    print(f"\nSummary: {valid_count}/{len(config['tickers'])} tickers validated")
    print(f"Valid tickers: {', '.join(ticker_list[:5])}..." if len(ticker_list) > 5 else f"Valid tickers: {', '.join(ticker_list)}")