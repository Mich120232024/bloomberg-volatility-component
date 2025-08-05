#!/usr/bin/env python3
"""
Check for NDF tickers using Bloomberg reference API
Tests known NDF ticker patterns directly
"""

import httpx
import asyncio
import json
from datetime import datetime
from typing import Dict, List

# Bloomberg API endpoint
BLOOMBERG_API_URL = "http://20.172.249.92:8080"
API_KEY = "test"

# Known NDF ticker patterns from Bloomberg documentation
NDF_PATTERNS = {
    "USDINR": [
        # Standard NDF format
        "NDFUSDINR1W Curncy", "NDFUSDINR2W Curncy", "NDFUSDINR1M Curncy", 
        "NDFUSDINR2M Curncy", "NDFUSDINR3M Curncy", "NDFUSDINR6M Curncy",
        "NDFUSDINR9M Curncy", "NDFUSDINR1Y Curncy", "NDFUSDINR2Y Curncy",
        # Alternative formats
        "IRN1W Curncy", "IRN2W Curncy", "IRN1M Curncy", "IRN2M Curncy",
        "IRN3M Curncy", "IRN6M Curncy", "IRN1Y Curncy"
    ],
    "USDTWD": [
        # NTN format for Taiwan NDF
        "NTN1W Curncy", "NTN2W Curncy", "NTN1M Curncy", "NTN2M Curncy",
        "NTN3M Curncy", "NTN6M Curncy", "NTN9M Curncy", "NTN1Y Curncy",
        "NTN2Y Curncy", "NTN3Y Curncy", "NTN5Y Curncy",
        # Alternative
        "NDFUSDTWD1M Curncy", "NDFUSDTWD3M Curncy", "NDFUSDTWD6M Curncy"
    ],
    "USDKRW": [
        # NKW format for Korea NDF
        "NKW1W Curncy", "NKW2W Curncy", "NKW1M Curncy", "NKW2M Curncy",
        "NKW3M Curncy", "NKW6M Curncy", "NKW9M Curncy", "NKW1Y Curncy",
        "NKW2Y Curncy", "NKW3Y Curncy", "NKW5Y Curncy",
        # Alternative
        "KRWN1M Curncy", "KRWN3M Curncy", "KRWN6M Curncy", "KRWN1Y Curncy"
    ],
    "USDIDR": [
        # IDN format for Indonesia NDF
        "IDN1W Curncy", "IDN2W Curncy", "IDN1M Curncy", "IDN2M Curncy",
        "IDN3M Curncy", "IDN6M Curncy", "IDN9M Curncy", "IDN1Y Curncy",
        # Alternative
        "NDFUSDIDR1M Curncy", "NDFUSDIDR3M Curncy", "NDFUSDIDR6M Curncy"
    ],
    "USDPHP": [
        # PHN format for Philippines NDF
        "PHN1W Curncy", "PHN2W Curncy", "PHN1M Curncy", "PHN2M Curncy",
        "PHN3M Curncy", "PHN6M Curncy", "PHN9M Curncy", "PHN1Y Curncy",
        # Alternative
        "PHPN1M Curncy", "PHPN3M Curncy", "PHPN6M Curncy", "PHPN1Y Curncy"
    ],
    "USDMYR": [
        # MRN format for Malaysia NDF
        "MRN1W Curncy", "MRN2W Curncy", "MRN1M Curncy", "MRN2M Curncy",
        "MRN3M Curncy", "MRN6M Curncy", "MRN9M Curncy", "MRN1Y Curncy",
        # Alternative
        "MYRN1M Curncy", "MYRN3M Curncy", "MYRN6M Curncy", "MYRN1Y Curncy"
    ],
    "USDBRL": [
        # BRN format for Brazil NDF
        "BRN1W Curncy", "BRN2W Curncy", "BRN1M Curncy", "BRN2M Curncy",
        "BRN3M Curncy", "BRN6M Curncy", "BRN9M Curncy", "BRN1Y Curncy",
        # Alternative DOL format
        "DOL1W Curncy", "DOL1M Curncy", "DOL3M Curncy", "DOL6M Curncy"
    ],
    "USDCLP": [
        # CLN format for Chile NDF
        "CLN1W Curncy", "CLN2W Curncy", "CLN1M Curncy", "CLN2M Curncy",
        "CLN3M Curncy", "CLN6M Curncy", "CLN9M Curncy", "CLN1Y Curncy",
        # Alternative
        "NDFUSDCLP1M Curncy", "NDFUSDCLP3M Curncy", "NDFUSDCLP6M Curncy"
    ],
    "USDPEN": [
        # PEN format for Peru NDF
        "PEN1W Curncy", "PEN2W Curncy", "PEN1M Curncy", "PEN2M Curncy",
        "PEN3M Curncy", "PEN6M Curncy", "PEN9M Curncy", "PEN1Y Curncy"
    ],
    "USDARS": [
        # ARN format for Argentina NDF
        "ARN1W Curncy", "ARN2W Curncy", "ARN1M Curncy", "ARN2M Curncy",
        "ARN3M Curncy", "ARN6M Curncy", "ARN9M Curncy", "ARN1Y Curncy",
        # Alternative ARS format
        "ARS1M Curncy", "ARS3M Curncy", "ARS6M Curncy", "ARS1Y Curncy"
    ]
}

class NDFChecker:
    def __init__(self):
        self.results = {}
        self.headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
    async def check_tickers(self, pair: str, tickers: List[str]):
        """Check a batch of tickers for a currency pair"""
        print(f"\n{'='*60}")
        print(f"Checking NDF tickers for {pair}")
        print('='*60)
        
        valid_tickers = []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Check in batches of 10
                for i in range(0, len(tickers), 10):
                    batch = tickers[i:i+10]
                    
                    payload = {
                        "securities": batch,
                        "fields": ["PX_LAST", "NAME", "LAST_UPDATE", "PX_BID", "PX_ASK"]
                    }
                    
                    response = await client.post(
                        f"{BLOOMBERG_API_URL}/api/bloomberg/reference",
                        json=payload,
                        headers=self.headers
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("success") and "data" in data:
                            securities_data = data["data"].get("securities_data", [])
                            
                            for item in securities_data:
                                if item.get("success") and item.get("fields"):
                                    ticker = item["security"]
                                    fields = item["fields"]
                                    
                                    if fields.get("PX_LAST") is not None:
                                        valid_tickers.append({
                                            "ticker": ticker,
                                            "px_last": fields["PX_LAST"],
                                            "name": fields.get("NAME", ""),
                                            "bid": fields.get("PX_BID"),
                                            "ask": fields.get("PX_ASK")
                                        })
                                        print(f"  ✓ {ticker}: {fields['PX_LAST']} ({fields.get('NAME', '')})")
                    
                    await asyncio.sleep(0.5)  # Rate limiting
        
        except Exception as e:
            print(f"  Error: {str(e)}")
        
        return valid_tickers
    
    async def check_all_ndfs(self):
        """Check all NDF patterns"""
        print("BLOOMBERG NDF TICKER VERIFICATION")
        print("="*80)
        print("Checking known NDF ticker patterns from Bloomberg documentation")
        print("="*80)
        
        for pair, tickers in NDF_PATTERNS.items():
            valid = await self.check_tickers(pair, tickers)
            self.results[pair] = {
                "tested": len(tickers),
                "valid": len(valid),
                "tickers": valid
            }
            await asyncio.sleep(1)
        
        self.generate_report()
    
    def generate_report(self):
        """Generate verification report"""
        print("\n" + "="*80)
        print("NDF TICKER VERIFICATION SUMMARY")
        print("="*80)
        
        successful = []
        failed = []
        
        for pair, data in self.results.items():
            if data["valid"] > 0:
                successful.append(pair)
            else:
                failed.append(pair)
        
        print(f"\n✅ CURRENCIES WITH WORKING NDF TICKERS ({len(successful)}):")
        for pair in successful:
            data = self.results[pair]
            print(f"\n{pair}: {data['valid']}/{data['tested']} tickers working")
            
            # Group by tenor
            by_tenor = {}
            for ticker_data in data["tickers"]:
                ticker = ticker_data["ticker"]
                # Extract tenor from ticker
                for tenor in ["1W", "2W", "1M", "2M", "3M", "6M", "9M", "1Y", "2Y", "3Y", "5Y"]:
                    if tenor in ticker:
                        by_tenor[tenor] = ticker_data
                        break
            
            # Show available tenors
            if by_tenor:
                print(f"  Available tenors: {', '.join(sorted(by_tenor.keys(), key=lambda x: ['1W','2W','1M','2M','3M','6M','9M','1Y','2Y','3Y','5Y'].index(x)))}")
                print("  Sample tickers:")
                for i, (tenor, ticker_data) in enumerate(list(by_tenor.items())[:3]):
                    print(f"    - {ticker_data['ticker']}: {ticker_data['px_last']}")
        
        print(f"\n❌ CURRENCIES WITHOUT WORKING NDF TICKERS ({len(failed)}):")
        for pair in failed:
            print(f"  - {pair}")
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"ndf_verification_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "results": self.results,
                "summary": {
                    "successful": successful,
                    "failed": failed,
                    "total_tested": len(self.results)
                }
            }, f, indent=2)
        
        print(f"\n📊 Detailed results saved to: {filename}")

async def main():
    checker = NDFChecker()
    await checker.check_all_ndfs()

if __name__ == "__main__":
    asyncio.run(main())