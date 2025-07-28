#!/usr/bin/env python3
"""
Bloomberg API Explorer - Discover available data and formats
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

class BloombergExplorer:
    def __init__(self):
        self.base_url = "http://20.172.249.92:8080"
        self.headers = {
            'Authorization': 'Bearer test',
            'Content-Type': 'application/json'
        }
        
    # REMOVED: explore_fx_rates - endpoint doesn't work and should not be used
    
    def explore_volatility_tickers(self):
        """Discover volatility ticker patterns"""
        print("\n🔍 Exploring Volatility Ticker Patterns")
        print("=" * 50)
        
        # Common FX pairs from health check
        pairs = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
        tenors = ["ON", "1W", "1M", "3M", "6M", "1Y"]
        
        all_tickers = []
        
        # Build ticker combinations
        for pair in pairs[:2]:  # First 2 pairs
            for tenor in tenors[:3]:  # First 3 tenors
                # ATM volatility
                if tenor == "ON":
                    all_tickers.append(f"{pair}V{tenor} Curncy")
                else:
                    all_tickers.append(f"{pair}V{tenor} BGN Curncy")
                
                # Risk Reversal 25D
                if tenor != "ON":
                    all_tickers.append(f"{pair}25R{tenor} BGN Curncy")
                    
                # Butterfly 25D
                if tenor != "ON":
                    all_tickers.append(f"{pair}25B{tenor} BGN Curncy")
        
        print(f"📝 Checking {len(all_tickers)} tickers in batches...")
        
        # Check in batches of 10
        batch_size = 10
        valid_tickers = []
        
        for i in range(0, len(all_tickers), batch_size):
            batch = all_tickers[i:i+batch_size]
            print(f"\n📦 Batch {i//batch_size + 1}: Checking {len(batch)} tickers")
            
            response = requests.post(
                f"{self.base_url}/api/bloomberg/reference",
                headers=self.headers,
                json={
                    "securities": batch,
                    "fields": ["PX_LAST", "PX_BID", "PX_ASK"]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'data' in data:
                    securities = data['data'].get('securities_data', [])
                    for sec in securities:
                        if sec.get('success') and sec.get('fields'):
                            if any(sec['fields'].get(f) is not None for f in ['PX_LAST', 'PX_BID', 'PX_ASK']):
                                valid_tickers.append(sec['security'])
                                print(f"  ✅ {sec['security']}: {sec['fields']}")
                            else:
                                print(f"  ⚠️  {sec['security']}: No data")
                        else:
                            print(f"  ❌ {sec['security']}: Failed")
        
        print(f"\n📊 Summary: {len(valid_tickers)} valid tickers found out of {len(all_tickers)} checked")
        return valid_tickers
    
    def explore_historical_data(self, ticker: str = "EURUSDV1M BGN Curncy"):
        """Explore historical data format"""
        print(f"\n🔍 Exploring Historical Data for {ticker}")
        print("=" * 50)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        response = requests.post(
            f"{self.base_url}/api/bloomberg/historical",
            headers=self.headers,
            json={
                "security": ticker,
                "fields": ["PX_LAST", "PX_BID", "PX_ASK"],
                "start_date": start_date.strftime("%Y%m%d"),
                "end_date": end_date.strftime("%Y%m%d"),
                "periodicity": "DAILY"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Response structure:")
            print(json.dumps(data, indent=2)[:1000])  # First 1000 chars
            
            if data.get('success') and 'data' in data:
                hist_data = data['data'].get('data', [])
                print(f"\n📊 Found {len(hist_data)} historical data points")
                if hist_data:
                    print(f"📅 Date range: {hist_data[0].get('date')} to {hist_data[-1].get('date')}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
    
    def discover_all_deltas(self, pair: str = "EURUSD", tenor: str = "1M"):
        """Discover all available delta strikes"""
        print(f"\n🔍 Discovering All Deltas for {pair} {tenor}")
        print("=" * 50)
        
        # Check all common deltas
        deltas = [5, 10, 15, 20, 25, 30, 35, 40, 45]
        tickers = []
        
        for delta in deltas:
            # Risk Reversal
            tickers.append(f"{pair}{delta}R{tenor} BGN Curncy")
            # Butterfly
            tickers.append(f"{pair}{delta}B{tenor} BGN Curncy")
        
        response = requests.post(
            f"{self.base_url}/api/bloomberg/reference",
            headers=self.headers,
            json={
                "securities": tickers,
                "fields": ["PX_LAST", "PX_BID", "PX_ASK"]
            }
        )
        
        valid_deltas = {"RR": [], "BF": []}
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and 'data' in data:
                for sec in data['data'].get('securities_data', []):
                    if sec.get('success') and sec.get('fields', {}).get('PX_LAST') is not None:
                        # Extract delta from ticker
                        import re
                        match = re.search(r'(\d+)(R|B)', sec['security'])
                        if match:
                            delta = int(match.group(1))
                            type_char = match.group(2)
                            if type_char == 'R':
                                valid_deltas['RR'].append(delta)
                            else:
                                valid_deltas['BF'].append(delta)
                            print(f"✅ Delta {delta}{'RR' if type_char == 'R' else 'BF'}: {sec['fields']['PX_LAST']}")
        
        print(f"\n📊 Valid Risk Reversal deltas: {sorted(valid_deltas['RR'])}")
        print(f"📊 Valid Butterfly deltas: {sorted(valid_deltas['BF'])}")
        
        return valid_deltas

def main():
    explorer = BloombergExplorer()
    
    # 1. Discover valid volatility tickers
    valid_tickers = explorer.explore_volatility_tickers()
    
    # 3. Check historical data
    if valid_tickers:
        explorer.explore_historical_data(valid_tickers[0])
    
    # 4. Discover all available deltas
    explorer.discover_all_deltas("EURUSD", "1M")
    
    # Save discovered data
    with open('bloomberg_discovery.json', 'w') as f:
        json.dump({
            'discovered_at': datetime.now().isoformat(),
            'valid_tickers': valid_tickers,
            'endpoints': {
                '/health': 'API health check',
                '/api/bloomberg/reference': 'Real-time market data (generic/reference)',
                '/api/bloomberg/historical': 'Historical time series'
            }
        }, f, indent=2)
    
    print("\n💾 Discovery results saved to bloomberg_discovery.json")

if __name__ == "__main__":
    main()