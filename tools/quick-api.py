#!/usr/bin/env python3
"""Quick API caller - simplified for debugging"""

import requests
import json
import sys

def call_api(endpoint, method="GET", data=None, direct=False):
    base_url = "http://20.172.249.92:8080" if direct else "http://localhost:3501"
    url = f"{base_url}{endpoint}"
    
    headers = {
        'Authorization': 'Bearer test',
        'Content-Type': 'application/json'
    }
    
    print(f"🔍 {method} {url}")
    
    if method == "POST":
        response = requests.post(url, json=data, headers=headers)
    else:
        response = requests.get(url, headers=headers)
    
    print(f"📥 Status: {response.status_code}")
    
    try:
        result = response.json()
        print(json.dumps(result, indent=2))
        return result
    except:
        print(response.text)
        return response.text

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 quick-api.py <endpoint> [POST] [--direct]")
        print("Example: python3 quick-api.py /api/bloomberg/reference POST")
        sys.exit(1)
    
    endpoint = sys.argv[1]
    method = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] in ["GET", "POST"] else "GET"
    direct = "--direct" in sys.argv
    
    # Default volatility surface request
    if method == "POST" and "reference" in endpoint:
        data = {
            "securities": [
                "EURUSDVON Curncy",
                "EURUSDV1W BGN Curncy", 
                "EURUSDV1M BGN Curncy",
                "EURUSD25R1M BGN Curncy",
                "EURUSD25B1M BGN Curncy"
            ],
            "fields": ["PX_LAST", "PX_BID", "PX_ASK"]
        }
    else:
        data = None
    
    call_api(endpoint, method, data, direct)