#!/usr/bin/env python3
import requests

bloomberg_url = "http://20.172.249.92:8080"

# Short rate patterns to test for each currency
short_rate_patterns = {
    'USD': {
        'deposits': ['USDR1T', 'USDR1W', 'USDR2W', 'USDR1M', 'USDR2M', 'USDR3M'],
        'fed_funds': ['FEDL01', 'FDFD', 'FDTR'],
        'bills': ['GB3', 'GB1M', 'GB3M', 'USGG3M', 'USGG1M'],
        'libor': ['US0001W', 'US0001M', 'US0003M']
    },
    'EUR': {
        'deposits': ['EUDR1T', 'EUDR1W', 'EUDR2W', 'EUDR1M', 'EUDR2M', 'EUDR3M'],
        'euribor': ['EUR001W', 'EUR001M', 'EUR003M'],
        'eonia': ['EONIA', 'EONIA1W'],
        'bills': ['GTEUR3M', 'GTEUR1M']
    },
    'GBP': {
        'deposits': ['BPDR1T', 'BPDR1W', 'BPDR2W', 'BPDR1M', 'BPDR2M', 'BPDR3M'],
        'libor': ['BP0001W', 'BP0001M', 'BP0003M'],
        'bills': ['GTGBP3M', 'GTGBP1M'],
        'sonia': ['SONIA1W', 'SONIA1M']
    },
    'JPY': {
        'deposits': ['JYDR1T', 'JYDR1W', 'JYDR2W', 'JYDR1M', 'JYDR2M', 'JYDR3M'],
        'tibor': ['JY0001W', 'JY0001M', 'JY0003M'],
        'bills': ['GTJPY3M', 'JGBS3M']
    },
    'CHF': {
        'deposits': ['SFDR1W', 'SFDR2W', 'SFDR1M', 'SFDR2M', 'SFDR3M'],
        'libor': ['SF0001W', 'SF0001M', 'SF0003M'],
        'saron': ['SARON1W', 'SARON1M', 'SARON3M']
    },
    'CAD': {
        'deposits': ['CDDR1W', 'CDDR2W', 'CDDR1M', 'CDDR2M', 'CDDR3M'],
        'bills': ['GTCAD3M', 'CTBB3M'],
        'ba': ['CDOR1W', 'CDOR1M', 'CDOR3M']
    },
    'AUD': {
        'deposits': ['ADBB1W', 'ADBB2W', 'ADBB3M', 'ADBB6M'],
        'bills': ['GTAUD3M', 'ATBB3M'],
        'libor': ['BBSW1W', 'BBSW1M', 'BBSW3M']
    },
    'NZD': {
        'deposits': ['NDBB1W', 'NDBB2W', 'NDBB3M'],
        'bills': ['GTNZD3M', 'NZBB3M']
    },
    'SEK': {
        'deposits': ['STIB1M', 'STIB3M', 'STIB6M'],
        'bills': ['GTSEK3M', 'SKBB3M'],
        'repo': ['SKREPO1W', 'SKREPO1M']
    },
    'NOK': {
        'deposits': ['NIBOR1M', 'NIBOR3M', 'NIBOR6M'],
        'bills': ['GTNOK3M', 'NKBB3M'],
        'nowa': ['NOWA1W', 'NOWA1M']
    }
}

suffixes = ['Curncy', 'Index', 'BGN Curncy', 'Govt']

for currency, patterns in short_rate_patterns.items():
    print(f"\n{'='*60}")
    print(f"{currency} Short Rates")
    print(f"{'='*60}")
    
    found_rates = []
    
    for rate_type, tickers in patterns.items():
        print(f"\n{rate_type.upper()}:")
        
        for ticker_base in tickers:
            for suffix in suffixes:
                ticker = f"{ticker_base} {suffix}"
                
                try:
                    response = requests.post(
                        f"{bloomberg_url}/api/bloomberg/reference",
                        headers={"Authorization": "Bearer test"},
                        json={
                            "securities": [ticker],
                            "fields": ["PX_LAST", "NAME", "CRNCY"]
                        },
                        timeout=2
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if "data" in data and "securities_data" in data["data"]:
                            for sec_data in data["data"]["securities_data"]:
                                if sec_data.get("success"):
                                    rate = sec_data["fields"].get("PX_LAST")
                                    name = sec_data["fields"].get("NAME", "")
                                    crncy = sec_data["fields"].get("CRNCY", "")
                                    
                                    if rate is not None and -5 < rate < 20:
                                        print(f"  ✓ {ticker}: {rate:.4f}% - {name}")
                                        found_rates.append({
                                            'ticker': ticker,
                                            'rate': rate,
                                            'name': name,
                                            'type': rate_type
                                        })
                                        break
                except:
                    pass
    
    print(f"\nFound {len(found_rates)} short-term rates for {currency}")