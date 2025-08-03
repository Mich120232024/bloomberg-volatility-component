#!/usr/bin/env python3
import requests
import time

bloomberg_url = "http://20.172.249.92:8080"

# G10 currencies to discover (excluding USD, EUR, GBP already done)
g10_currencies = ['JPY', 'CHF', 'CAD', 'AUD', 'NZD', 'SEK', 'NOK']

# Known OIS patterns for each currency
ois_patterns = {
    'JPY': {
        'overnight': ['TONAR Index', 'MUTKCALM Index', 'JYDR1T Curncy'],
        'swaps': ['JYSO', 'JPSW'],
        'prefixes': ['JYSO', 'JPSW', 'S0166']
    },
    'CHF': {
        'overnight': ['SARON Index', 'SFDR1T Curncy', 'SSARON Index'],
        'swaps': ['SFSW', 'SFSO'],
        'prefixes': ['SFSO', 'SFSW', 'S0021']
    },
    'CAD': {
        'overnight': ['CAONREPO Index', 'CDOR1M Index', 'CDDR1T Curncy'],
        'swaps': ['CDSW', 'CDSO'],
        'prefixes': ['CDSO', 'CDSW', 'S0017']
    },
    'AUD': {
        'overnight': ['RBACOR Index', 'RBA30 Index', 'ADBB1M Index'],
        'swaps': ['ADSW', 'ADSO'],
        'prefixes': ['ADSO', 'ADSW', 'S0003']
    },
    'NZD': {
        'overnight': ['NZOCRS Index', 'NDBB1M Index'],
        'swaps': ['NDSW', 'NDSO'],
        'prefixes': ['NDSO', 'NDSW', 'S0176']
    },
    'SEK': {
        'overnight': ['STIBOR1D Index', 'STIB1W Index', 'SKDR1T Curncy'],
        'swaps': ['SKSW', 'SKSO'],
        'prefixes': ['SKSO', 'SKSW', 'S0018']
    },
    'NOK': {
        'overnight': ['NIBOR1D Index', 'NIBOR1W Index', 'NKDR1T Curncy'],
        'swaps': ['NKSW', 'NKSO'],
        'prefixes': ['NKSO', 'NKSW', 'S0184']
    }
}

# Tenor patterns to test
short_tenors = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K']  # 1M-11M
long_tenors = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20, 25, 30, 40, 50]  # Years
monthly_tenors = ['001W', '002W', '003W', '001M', '002M', '003M', '006M', '009M', '012M']

all_results = {}

for currency in g10_currencies:
    print(f"\n{'='*60}")
    print(f"Discovering {currency} OIS tickers...")
    print(f"{'='*60}")
    
    currency_results = {
        'overnight': [],
        'swaps': []
    }
    
    # Test overnight tickers
    print(f"\nTesting {currency} overnight rates...")
    for ticker in ois_patterns[currency]['overnight']:
        try:
            response = requests.post(
                f"{bloomberg_url}/api/bloomberg/reference",
                headers={"Authorization": "Bearer test"},
                json={
                    "securities": [ticker],
                    "fields": ["PX_LAST", "NAME", "CRNCY"]
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and "securities_data" in data["data"]:
                    for sec_data in data["data"]["securities_data"]:
                        if sec_data.get("success"):
                            rate = sec_data["fields"].get("PX_LAST")
                            name = sec_data["fields"].get("NAME", "")
                            crncy = sec_data["fields"].get("CRNCY", "")
                            
                            if rate is not None and -2 < rate < 20:  # Reasonable rate range
                                print(f"  ✓ {ticker}: {rate:.4f}% - {name}")
                                currency_results['overnight'].append({
                                    'ticker': ticker,
                                    'rate': rate,
                                    'name': name
                                })
                                break  # Found working overnight, stop testing
        except Exception as e:
            print(f"  ✗ {ticker}: Error - {e}")
    
    # Test swap patterns
    print(f"\nTesting {currency} swap patterns...")
    for prefix in ois_patterns[currency]['prefixes']:
        found_pattern = False
        
        # Test short tenors first
        for tenor in short_tenors[:3]:  # Test A, B, C
            ticker = f"{prefix}{tenor} Curncy"
            try:
                response = requests.post(
                    f"{bloomberg_url}/api/bloomberg/reference",
                    headers={"Authorization": "Bearer test"},
                    json={
                        "securities": [ticker],
                        "fields": ["PX_LAST", "NAME"]
                    },
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "data" in data and "securities_data" in data["data"]:
                        for sec_data in data["data"]["securities_data"]:
                            if sec_data.get("success"):
                                rate = sec_data["fields"].get("PX_LAST")
                                if rate is not None and -2 < rate < 20:
                                    print(f"  ✓ Pattern {prefix} works! Found {ticker}: {rate:.4f}%")
                                    found_pattern = True
                                    break
            except:
                pass
            
            if found_pattern:
                break
        
        if found_pattern:
            # Test a few more tenors to confirm
            test_tickers = []
            
            # Monthly tenors
            for tenor in short_tenors:
                test_tickers.append(f"{prefix}{tenor} Curncy")
            
            # Yearly tenors
            for year in [1, 2, 3, 5, 10, 20, 30]:
                test_tickers.append(f"{prefix}{year} Curncy")
            
            valid_count = 0
            for ticker in test_tickers[:20]:  # Test up to 20 tickers
                try:
                    response = requests.post(
                        f"{bloomberg_url}/api/bloomberg/reference",
                        headers={"Authorization": "Bearer test"},
                        json={
                            "securities": [ticker],
                            "fields": ["PX_LAST"]
                        },
                        timeout=3
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if "data" in data and "securities_data" in data["data"]:
                            for sec_data in data["data"]["securities_data"]:
                                if sec_data.get("success") and sec_data["fields"].get("PX_LAST") is not None:
                                    valid_count += 1
                                    currency_results['swaps'].append({
                                        'ticker': ticker,
                                        'prefix': prefix
                                    })
                except:
                    pass
            
            print(f"    Found {valid_count} valid tickers with pattern {prefix}")
    
    all_results[currency] = currency_results
    time.sleep(1)  # Rate limiting

# Summary
print(f"\n{'='*60}")
print("DISCOVERY SUMMARY")
print(f"{'='*60}")

for currency, results in all_results.items():
    overnight = results['overnight']
    swaps = results['swaps']
    
    print(f"\n{currency}:")
    if overnight:
        print(f"  Overnight: {overnight[0]['ticker']} ({overnight[0]['rate']:.4f}%)")
    else:
        print(f"  Overnight: NOT FOUND")
    
    if swaps:
        # Get unique prefixes
        prefixes = list(set([s['prefix'] for s in swaps]))
        print(f"  Swap pattern: {prefixes[0]} (found {len(swaps)} tickers)")
    else:
        print(f"  Swap pattern: NOT FOUND")