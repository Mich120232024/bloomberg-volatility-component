#!/usr/bin/env python3
import requests

bloomberg_url = "http://20.172.249.92:8080"

# Test patterns for CHF, SEK, NOK
test_patterns = {
    'CHF': {
        'overnight': ['SSARON Index', 'SFDR1T Curncy', 'TOMNEXT Index'],
        'patterns': [
            ('SFSO', [1, 2, 3, 5, 10]),  # Swiss OIS
            ('SFSW', [1, 2, 3, 5, 10]),  # Swiss swaps
            ('S0021Z', [1, 2, 3, 5, 10]), # Bloomberg curve
            ('SARON', [1, 3, 6, 12]),     # SARON-based
            ('CHSO', [1, 2, 3, 5, 10]),  # Alternative pattern
        ]
    },
    'SEK': {
        'overnight': ['STIBOR1D Index', 'STIB1W Index', 'SEKON Index'],
        'patterns': [
            ('SKSO', [1, 2, 3, 5, 10]),   # SEK OIS
            ('SKSW', [1, 2, 3, 5, 10]),   # SEK swaps  
            ('S0018Z', [1, 2, 3, 5, 10]), # Bloomberg curve
            ('SESO', [1, 2, 3, 5, 10]),   # Alternative
            ('STIB', ['3M', '6M']),        # STIBOR-based
        ]
    },
    'NOK': {
        'overnight': ['NIBOR1D Index', 'NIBOR1W Index', 'NOWA Index'],
        'patterns': [
            ('NKSO', [1, 2, 3, 5, 10]),   # NOK OIS
            ('NKSW', [1, 2, 3, 5, 10]),   # NOK swaps
            ('S0184Z', [1, 2, 3, 5, 10]), # Bloomberg curve
            ('NOSO', [1, 2, 3, 5, 10]),   # Alternative
            ('NOWO', [1, 2, 3, 5, 10]),   # NOWA-based
        ]
    }
}

# Also verify correct CHF overnight
print("Verifying CHF overnight rates...")
print("="*60)

chf_overnight_tests = [
    'SSARON Index',
    'TOMNEXT Index', 
    'SFDR1T Curncy',
    'SARON T/N Index',
    'SARON ON Index'
]

for ticker in chf_overnight_tests:
    try:
        response = requests.post(
            f"{bloomberg_url}/api/bloomberg/reference",
            headers={"Authorization": "Bearer test"},
            json={
                "securities": [ticker],
                "fields": ["PX_LAST", "NAME", "CRNCY", "DESCRIPTION"]
            },
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "securities_data" in data["data"]:
                for sec_data in data["data"]["securities_data"]:
                    if sec_data.get("success"):
                        fields = sec_data["fields"]
                        rate = fields.get("PX_LAST")
                        name = fields.get("NAME", "")
                        crncy = fields.get("CRNCY", "")
                        desc = fields.get("DESCRIPTION", "")
                        
                        if rate is not None:
                            print(f"{ticker}: {rate:.4f}% - {name} [{crncy}]")
                            if desc:
                                print(f"  Description: {desc}")
    except Exception as e:
        print(f"Error testing {ticker}: {e}")

# Now test swap patterns
for currency, config in test_patterns.items():
    print(f"\n{'='*60}")
    print(f"Testing {currency} swap patterns...")
    print(f"{'='*60}")
    
    found_patterns = []
    
    for prefix, tenors in config['patterns']:
        # Test first tenor
        test_tenor = tenors[0] if tenors else 1
        
        # Try different formats
        test_tickers = []
        if isinstance(test_tenor, str):
            test_tickers = [
                f"{prefix} {test_tenor} Curncy",
                f"{prefix}{test_tenor} Curncy",
                f"{prefix} {test_tenor} Index"
            ]
        else:
            test_tickers = [
                f"{prefix}{test_tenor} Curncy",
                f"{prefix}0{test_tenor} Curncy" if test_tenor < 10 else f"{prefix}{test_tenor} Curncy",
                f"{prefix} {test_tenor}Y Curncy",
                f"{prefix}{test_tenor}Y Curncy"
            ]
        
        for ticker in test_tickers:
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
                                
                                if rate is not None and -5 < rate < 20:
                                    print(f"✓ Found pattern {prefix}: {ticker} = {rate:.4f}% - {name}")
                                    found_patterns.append(prefix)
                                    break
            except:
                pass
            
            if prefix in found_patterns:
                break
    
    if not found_patterns:
        print(f"✗ No swap patterns found for {currency}")

# Test specific Bloomberg curve tickers
print(f"\n{'='*60}")
print("Testing Bloomberg curve tickers...")
print(f"{'='*60}")

curve_tickers = [
    'S0021Z1 Index',  # CHF 1Y
    'S0021Z5 Index',  # CHF 5Y
    'S0018Z1 Index',  # SEK 1Y
    'S0018Z5 Index',  # SEK 5Y
    'S0184Z1 Index',  # NOK 1Y
    'S0184Z5 Index',  # NOK 5Y
]

for ticker in curve_tickers:
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
                        
                        if rate is not None:
                            print(f"✓ {ticker}: {rate:.4f}% - {name} [{crncy}]")
    except:
        pass