#!/usr/bin/env python3
import requests

bloomberg_url = "http://20.172.249.92:8080"

# Test various GBP OIS ticker patterns
# SONIA = Sterling Overnight Index Average
test_patterns = [
    # GBP OIS patterns
    ("BPSW", [1, 3, 6, 9]),  # BP = British Pound
    ("BPSO", ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]),  # Short end
    ("BPSO", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20, 25, 30]),  # Long end
    
    # SONIA patterns
    ("SONIO", [1, 3, 6, 9, 12]),  # SONIA OIS
    ("SONIA", ["ON", 1, 3, 6, 9, 12]),
    
    # GBP money market
    ("GBP", ["001W", "002W", "003W", "001M", "002M", "003M", "006M", "009M", "012M"]),
    
    # Alternative patterns
    ("GPSW", [1, 2, 3, 4, 5, 7, 10, 15, 20, 30]),
    ("S0006", [1, 2, 3, 4, 5, 7, 10, 15, 20, 30]),  # Bloomberg curve codes
    
    # Short maturity patterns
    ("GBDR", ["1T", "1W", "2W", "3W", "1M", "2M", "3M"]),
]

suffixes = ["Curncy", "Index", "BGN Curncy"]

print("Searching for GBP OIS tickers...")
print("=" * 60)

found_tickers = []

for prefix, tenors in test_patterns:
    print(f"\nTesting {prefix} pattern...")
    pattern_found = False
    
    for tenor in tenors[:5]:  # Test first 5 to check pattern
        for suffix in suffixes:
            # Try different formatting
            if isinstance(tenor, str):
                tickers_to_test = [
                    f"{prefix}{tenor} {suffix}",      # SONIOON Curncy
                    f"{prefix} {tenor} {suffix}",      # SONIA ON Curncy
                ]
            else:
                tickers_to_test = [
                    f"{prefix}{tenor} {suffix}",       # BPSO1 Curncy
                    f"{prefix}0{tenor} {suffix}" if tenor < 10 else f"{prefix}{tenor} {suffix}",  # BPSO01 Curncy
                ]
            
            for ticker in tickers_to_test:
                response = requests.post(
                    f"{bloomberg_url}/api/bloomberg/reference",
                    headers={"Authorization": "Bearer test"},
                    json={
                        "securities": [ticker],
                        "fields": ["PX_LAST", "NAME", "CRNCY"]
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "data" in data and "securities_data" in data["data"]:
                        for sec_data in data["data"]["securities_data"]:
                            if sec_data.get("success") and sec_data.get("fields", {}).get("PX_LAST") is not None:
                                rate = sec_data["fields"]["PX_LAST"]
                                name = sec_data["fields"].get("NAME", "")
                                crncy = sec_data["fields"].get("CRNCY", "")
                                
                                # Check if rate is reasonable (between -1% and 10%)
                                if -1 < rate < 10 and crncy == "GBP":
                                    print(f"  ✓ {ticker}: {rate:.4f}% - {name}")
                                    found_tickers.append((ticker, tenor, rate))
                                    pattern_found = True
                                    break
                
                if pattern_found:
                    break

# Also test specific known GBP tickers
print("\n" + "=" * 60)
print("Testing specific GBP tickers...")

specific_tickers = [
    # SONIA overnight
    "SONIARON Index",
    "SONIA Index",
    "GBDR1T Curncy",
    
    # GBP short end
    "GBP001W Index",
    "GBP001M Index", 
    "GBP003M Index",
    "GBP006M Index",
    
    # GBP OIS swaps
    "BPSOA Curncy",
    "BPSOB Curncy",
    "BPSOC Curncy",
    "BPSOD Curncy",
    "BPSOE Curncy",
    "BPSOF Curncy",
    "BPSOG Curncy",
    "BPSOH Curncy",
    "BPSOI Curncy",
    "BPSOJ Curncy",
    "BPSO1 Curncy",
    "BPSO2 Curncy",
    "BPSO3 Curncy",
    "BPSO4 Curncy",
    "BPSO5 Curncy",
    "BPSO7 Curncy",
    "BPSO10 Curncy",
    "BPSO15 Curncy",
    "BPSO20 Curncy",
    "BPSO25 Curncy",
    "BPSO30 Curncy",
]

for ticker in specific_tickers:
    response = requests.post(
        f"{bloomberg_url}/api/bloomberg/reference",
        headers={"Authorization": "Bearer test"},
        json={
            "securities": [ticker],
            "fields": ["PX_LAST", "NAME", "DESCRIPTION", "CRNCY"]
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        if "data" in data and "securities_data" in data["data"]:
            for sec_data in data["data"]["securities_data"]:
                if sec_data.get("success"):
                    fields = sec_data.get("fields", {})
                    rate = fields.get("PX_LAST")
                    if rate is not None and -1 < rate < 10:
                        name = fields.get("NAME", "")
                        crncy = fields.get("CRNCY", "")
                        print(f"✓ {ticker}: {rate:.4f}% - {name} [{crncy}]")
                        found_tickers.append((ticker, "specific", rate))

print("\n" + "=" * 60)
print(f"Summary: Found {len(found_tickers)} valid GBP tickers")
if found_tickers:
    print("\nValid tickers:")
    for ticker, tenor, rate in found_tickers:
        print(f"  {ticker}: {rate:.4f}%")