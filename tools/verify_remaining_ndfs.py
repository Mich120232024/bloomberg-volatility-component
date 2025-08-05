#!/usr/bin/env python3
"""
Verify remaining NDF patterns and fix incorrect mappings
"""

import httpx
import asyncio
import json
from datetime import datetime
from typing import Dict, List

# Bloomberg API endpoint
BLOOMBERG_API_URL = "http://20.172.249.92:8080"
API_KEY = "test"

# Additional NDF patterns to check
ADDITIONAL_PATTERNS = {
    "USDKRW": [
        # Korean Won NDFs - alternative patterns
        "KWN1W Curncy", "KWN2W Curncy", "KWN1M Curncy", "KWN2M Curncy",
        "KWN3M Curncy", "KWN6M Curncy", "KWN9M Curncy", "KWN1Y Curncy",
        "KWN2Y Curncy", "KWN3Y Curncy", "KWN5Y Curncy",
        # NDKO format
        "NDKO1W Curncy", "NDKO1M Curncy", "NDKO3M Curncy", "NDKO6M Curncy",
        "NDKO1Y Curncy", "NDKO2Y Curncy"
    ],
    "USDIDR": [
        # Indonesian Rupiah NDFs - alternative patterns
        "IHN1W Curncy", "IHN2W Curncy", "IHN1M Curncy", "IHN2M Curncy",
        "IHN3M Curncy", "IHN6M Curncy", "IHN9M Curncy", "IHN1Y Curncy",
        # NDID format
        "NDID1W Curncy", "NDID1M Curncy", "NDID3M Curncy", "NDID6M Curncy"
    ],
    "USDPHP": [
        # Philippine Peso NDFs - alternative patterns
        "PPN1W Curncy", "PPN2W Curncy", "PPN1M Curncy", "PPN2M Curncy",
        "PPN3M Curncy", "PPN6M Curncy", "PPN9M Curncy", "PPN1Y Curncy",
        # NDPH format
        "NDPH1W Curncy", "NDPH1M Curncy", "NDPH3M Curncy", "NDPH6M Curncy"
    ],
    "USDBRL": [
        # Brazilian Real NDFs - additional patterns
        "BCN1W Curncy", "BCN2W Curncy", "BCN1M Curncy", "BCN2M Curncy",
        "BCN3M Curncy", "BCN6M Curncy", "BCN9M Curncy", "BCN1Y Curncy",
        # NDBR format
        "NDBR1W Curncy", "NDBR1M Curncy", "NDBR3M Curncy", "NDBR6M Curncy",
        # BRL format (onshore forwards)
        "BRL1W Curncy", "BRL1M Curncy", "BRL3M Curncy", "BRL6M Curncy"
    ],
    "USDCLP": [
        # Chilean Peso NDFs - fix CLP vs COP issue
        "CHN1W Curncy", "CHN2W Curncy", "CHN1M Curncy", "CHN2M Curncy",
        "CHN3M Curncy", "CHN6M Curncy", "CHN9M Curncy", "CHN1Y Curncy",
        # CLP forwards
        "CLP1W Curncy", "CLP1M Curncy", "CLP3M Curncy", "CLP6M Curncy"
    ],
    "USDCOP": [
        # Colombian Peso NDFs - these are what CLN actually represents
        "CLN1W Curncy", "CLN2W Curncy", "CLN1M Curncy", "CLN2M Curncy",
        "CLN3M Curncy", "CLN6M Curncy", "CLN9M Curncy", "CLN1Y Curncy",
        "CLN2Y Curncy", "CLN3Y Curncy"
    ],
    "USDPEN": [
        # Peruvian Sol NDFs - alternative patterns
        "PEO1W Curncy", "PEO2W Curncy", "PEO1M Curncy", "PEO2M Curncy",
        "PEO3M Curncy", "PEO6M Curncy", "PEO9M Curncy", "PEO1Y Curncy",
        # NDPE format
        "NDPE1W Curncy", "NDPE1M Curncy", "NDPE3M Curncy", "NDPE6M Curncy"
    ],
    "USDARS": [
        # Argentine Peso NDFs - alternative patterns
        "AFN1W Curncy", "AFN2W Curncy", "AFN1M Curncy", "AFN2M Curncy",
        "AFN3M Curncy", "AFN6M Curncy", "AFN9M Curncy", "AFN1Y Curncy",
        # NDAR format
        "NDAR1W Curncy", "NDAR1M Curncy", "NDAR3M Curncy", "NDAR6M Curncy",
        # ARS Blue Chip Swap
        "ARS1M BCS Curncy", "ARS3M BCS Curncy", "ARS6M BCS Curncy"
    ]
}

class NDFVerifier:
    def __init__(self):
        self.results = {}
        self.headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
    async def check_tickers(self, pair: str, tickers: List[str]):
        """Check a batch of tickers"""
        print(f"\n{'='*60}")
        print(f"Verifying tickers for {pair}")
        print('='*60)
        
        valid_tickers = []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Check all tickers in one batch
                payload = {
                    "securities": tickers,
                    "fields": ["PX_LAST", "NAME", "PX_BID", "PX_ASK"]
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
        
        except Exception as e:
            print(f"  Error: {str(e)}")
        
        return valid_tickers
    
    async def verify_all(self):
        """Verify all additional NDF patterns"""
        print("BLOOMBERG NDF ADDITIONAL PATTERN VERIFICATION")
        print("="*80)
        print("Checking additional NDF patterns and fixing mappings")
        print("="*80)
        
        for pair, tickers in ADDITIONAL_PATTERNS.items():
            valid = await self.check_tickers(pair, tickers)
            self.results[pair] = {
                "tested": len(tickers),
                "valid": len(valid),
                "tickers": valid
            }
            await asyncio.sleep(1)
        
        self.generate_report()
    
    def generate_report(self):
        """Generate final report"""
        print("\n" + "="*80)
        print("FINAL NDF TICKER SUMMARY")
        print("="*80)
        
        # Combine with previous results
        previous_working = {
            "USDINR": "IRN format (5 tenors: 1W-6M)",
            "USDTWD": "NTN format (10 tenors: 1W-5Y)",
            "USDMYR": "MRN format (6 tenors: 1W-9M)",
            "USDCOP": "CLN format (7+ tenors: 1W-3Y)"  # CLN is actually COP not CLP!
        }
        
        print("\n✅ COMPLETE NDF TICKER MAPPING:")
        
        # Print all working NDFs
        all_working = {}
        
        # Add previous results
        for pair, desc in previous_working.items():
            all_working[pair] = desc
            print(f"\n{pair}: {desc}")
        
        # Add new discoveries
        for pair, data in self.results.items():
            if data["valid"] > 0 and pair not in all_working:
                # Find the working format
                formats = set()
                for ticker_data in data["tickers"]:
                    ticker = ticker_data["ticker"]
                    # Extract format
                    for fmt in ["KWN", "IHN", "PPN", "BCN", "CHN", "PEO", "AFN", "BRL", "CLP"]:
                        if fmt in ticker:
                            formats.add(fmt)
                            break
                
                if formats:
                    format_str = "/".join(formats)
                    tenor_count = len(data["tickers"])
                    all_working[pair] = f"{format_str} format ({tenor_count} tenors)"
                    print(f"\n{pair}: {format_str} format ({tenor_count} tenors found)")
                    # Show sample tickers
                    for ticker_data in data["tickers"][:3]:
                        print(f"  - {ticker_data['ticker']}: {ticker_data['px_last']}")
        
        # List still missing
        all_pairs = set(ADDITIONAL_PATTERNS.keys()) | set(previous_working.keys())
        missing = [p for p in all_pairs if p not in all_working]
        
        if missing:
            print(f"\n❌ STILL NO NDF TICKERS FOUND ({len(missing)}):")
            for pair in missing:
                print(f"  - {pair}")
        
        # Summary table
        print("\n" + "="*80)
        print("RECOMMENDED NDF TICKER FORMATS:")
        print("="*80)
        print("\n| Currency Pair | NDF Format | Example Ticker    | Coverage |")
        print("|---------------|------------|-------------------|----------|")
        print("| USDINR        | IRN        | IRN1M Curncy      | 1W-6M    |")
        print("| USDTWD        | NTN        | NTN1M Curncy      | 1W-5Y    |")
        print("| USDMYR        | MRN        | MRN1M Curncy      | 1W-9M    |")
        print("| USDCOP        | CLN        | CLN1M Curncy      | 1W-3Y    |")
        
        # Add new discoveries to table
        format_map = {
            "USDKRW": ("KWN", "KWN1M Curncy"),
            "USDIDR": ("IHN", "IHN1M Curncy"),
            "USDPHP": ("PPN", "PPN1M Curncy"),
            "USDBRL": ("BCN/BRL", "BCN1M Curncy"),
            "USDCLP": ("CHN/CLP", "CHN1M Curncy"),
            "USDPEN": ("PEO", "PEO1M Curncy"),
            "USDARS": ("AFN", "AFN1M Curncy")
        }
        
        for pair, data in self.results.items():
            if data["valid"] > 0 and pair in format_map:
                fmt, example = format_map[pair]
                coverage = self.get_coverage_string(data["tickers"])
                print(f"| {pair}        | {fmt:<10} | {example:<17} | {coverage:<8} |")
        
        # Save complete results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"ndf_complete_mapping_{timestamp}.json"
        
        complete_results = {
            "timestamp": datetime.now().isoformat(),
            "working_ndfs": all_working,
            "detailed_results": self.results,
            "ticker_formats": {
                "USDINR": {"format": "IRN", "example": "IRN1M Curncy"},
                "USDTWD": {"format": "NTN", "example": "NTN1M Curncy"},
                "USDMYR": {"format": "MRN", "example": "MRN1M Curncy"},
                "USDCOP": {"format": "CLN", "example": "CLN1M Curncy"}
            }
        }
        
        # Add new formats
        for pair, data in self.results.items():
            if data["valid"] > 0 and pair in format_map:
                fmt, example = format_map[pair]
                complete_results["ticker_formats"][pair] = {
                    "format": fmt,
                    "example": example,
                    "working_tickers": [t["ticker"] for t in data["tickers"]]
                }
        
        with open(filename, 'w') as f:
            json.dump(complete_results, f, indent=2)
        
        print(f"\n📊 Complete NDF mapping saved to: {filename}")
    
    def get_coverage_string(self, tickers: List[Dict]) -> str:
        """Get coverage string from ticker list"""
        tenors = []
        for ticker_data in tickers:
            ticker = ticker_data["ticker"]
            for tenor in ["1W", "2W", "1M", "2M", "3M", "6M", "9M", "1Y", "2Y", "3Y", "5Y"]:
                if tenor in ticker:
                    tenors.append(tenor)
                    break
        
        if not tenors:
            return "Unknown"
        
        # Sort tenors
        tenor_order = ["1W", "2W", "1M", "2M", "3M", "6M", "9M", "1Y", "2Y", "3Y", "5Y"]
        sorted_tenors = sorted(set(tenors), key=lambda x: tenor_order.index(x) if x in tenor_order else 99)
        
        if len(sorted_tenors) > 2:
            return f"{sorted_tenors[0]}-{sorted_tenors[-1]}"
        else:
            return ", ".join(sorted_tenors)

async def main():
    verifier = NDFVerifier()
    await verifier.verify_all()

if __name__ == "__main__":
    asyncio.run(main())