#!/usr/bin/env python3
"""
Simple script to update Bloomberg ticker discovery patterns to text-based search
"""

# The key changes needed:
# OLD: "USD": "USSO* Curncy OR SOFR* Index"
# NEW: "USD": "USD OIS"

old_patterns = {
    '"USD": "USSO* Curncy OR SOFR* Index"': '"USD": "USD OIS"',
    '"EUR": "EURON* Curncy OR ESTR* Index"': '"EUR": "EUR OIS"',
    '"GBP": "SONIO* Index OR SONIA* Index"': '"GBP": "GBP OIS"',
    '"JPY": "JYSO* Curncy OR TONA* Index OR MTON* Index"': '"JPY": "JPY OIS"',
    '"CHF": "SSARA* Curncy OR SARON* Index"': '"CHF": "CHF OIS"',
    '"CAD": "CDOR* Curncy OR CORRA* Index"': '"CAD": "CAD OIS"',
    '"AUD": "RBACOR* Curncy OR AONIA* Index"': '"AUD": "AUD OIS"'
}

# Read the file
with open(r'C:\BloombergAPI\ticker_discovery_module.py', 'r') as f:
    content = f.read()

# Apply replacements
for old, new in old_patterns.items():
    content = content.replace(old, new)

# Write back
with open(r'C:\BloombergAPI\ticker_discovery_module.py', 'w') as f:
    f.write(content)

print("Successfully updated search patterns to text-based search")