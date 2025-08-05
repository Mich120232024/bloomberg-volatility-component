#!/usr/bin/env python3
"""
Currency Forward Data Coverage Analysis
Analyzes Bloomberg forward curve data availability for all currency pairs
"""

import httpx
import asyncio
import json
from datetime import datetime
from typing import Dict, List
import sys

# Bloomberg Gateway URL - Real API endpoint
BLOOMBERG_API_URL = "http://20.172.249.92:8080"

# Standard forward tenors used in FX markets
FORWARD_TENORS = ["1W", "2W", "1M", "2M", "3M", "6M", "9M", "1Y", "18M", "2Y", "3Y", "5Y"]

# Currency pairs organized by category
CURRENCY_PAIRS = {
    "G10": ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD", "USDSEK", "USDNOK", "USDDKK"],
    "EM_ASIA": ["USDSGD", "USDHKD", "USDCNH", "USDINR", "USDKRW", "USDTWD", "USDTHB", "USDPHP", "USDIDR", "USDMYR"],
    "EM_LATAM": ["USDMXN", "USDBRL", "USDCLP", "USDCOP", "USDPEN", "USDARS"],
    "EM_EMEA": ["USDZAR", "USDTRY", "USDRUB", "USDPLN", "USDHUF", "USDCZK", "USDILS", "USDAED", "USDSAR"],
    "CROSSES": ["EURGBP", "EURJPY", "GBPJPY", "EURCHF", "AUDJPY", "CADJPY", "EURAUD", "EURNZD", "GBPAUD", "GBPNZD"]
}

class ForwardDataAnalyzer:
    def __init__(self):
        self.results = {}
        self.categories = {
            "full_5y": [],      # Has all tenors including 5Y
            "full_3y": [],      # Has all tenors up to 3Y
            "partial_long": [], # Has some data beyond 1Y
            "partial_short": [], # Only has data up to 1Y
            "spot_only": [],    # Only spot available
            "no_data": []       # No data at all
        }
        
    async def analyze_pair(self, pair: str, category: str) -> Dict:
        """Analyze forward data availability for a currency pair"""
        print(f"\nAnalyzing {pair} ({category})...")
        
        # Build Bloomberg tickers
        spot_ticker = f"{pair} Curncy"
        forward_tickers = [f"{pair}{tenor} Curncy" for tenor in FORWARD_TENORS]
        all_tickers = [spot_ticker] + forward_tickers
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {
                    "Authorization": "Bearer test",  # Bloomberg API auth
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "securities": all_tickers,
                    "fields": ["PX_LAST", "NAME", "LAST_UPDATE"]
                }
                
                response = await client.post(
                    f"{BLOOMBERG_API_URL}/api/bloomberg/reference",
                    json=payload,
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return self.process_response(pair, category, data)
                else:
                    print(f"  ❌ API returned status {response.status_code}")
                    return {"pair": pair, "category": category, "status": "error"}
                    
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            return {"pair": pair, "category": category, "status": "error", "error": str(e)}
    
    def process_response(self, pair: str, category: str, response: Dict) -> Dict:
        """Process Bloomberg API response"""
        result = {
            "pair": pair,
            "category": category,
            "has_spot": False,
            "available_forwards": [],
            "missing_forwards": [],
            "longest_tenor": None,
            "data_points": {}
        }
        
        if response.get("success") and "data" in response:
            security_data = response["data"].get("securities_data", [])
            
            for item in security_data:
                if item.get("success") and item.get("fields"):
                    ticker = item["security"]
                    fields = item["fields"]
                    
                    if fields.get("PX_LAST") is not None:
                        if ticker == f"{pair} Curncy":
                            result["has_spot"] = True
                            result["data_points"]["SPOT"] = fields["PX_LAST"]
                            print(f"  ✓ Spot rate: {fields['PX_LAST']}")
                        else:
                            # Extract tenor
                            tenor = ticker.replace(pair, "").replace(" Curncy", "").strip()
                            if tenor in FORWARD_TENORS:
                                result["available_forwards"].append(tenor)
                                result["data_points"][tenor] = fields["PX_LAST"]
        
        # Identify missing tenors
        for tenor in FORWARD_TENORS:
            if tenor not in result["available_forwards"]:
                result["missing_forwards"].append(tenor)
        
        # Determine longest available tenor
        if result["available_forwards"]:
            tenor_days = {
                "1W": 7, "2W": 14, "1M": 30, "2M": 60, "3M": 90,
                "6M": 180, "9M": 270, "1Y": 365, "18M": 545,
                "2Y": 730, "3Y": 1095, "5Y": 1825
            }
            sorted_tenors = sorted(result["available_forwards"], 
                                 key=lambda x: tenor_days.get(x, 0))
            result["longest_tenor"] = sorted_tenors[-1]
        
        # Categorize the pair
        self.categorize_pair(pair, result)
        
        # Print summary
        if result["available_forwards"]:
            print(f"  ✓ Forward data: {len(result['available_forwards'])} tenors (max: {result['longest_tenor']})")
        elif result["has_spot"]:
            print(f"  ⚠️  Spot only - no forward data")
        else:
            print(f"  ❌ No data available")
        
        return result
    
    def categorize_pair(self, pair: str, result: Dict):
        """Categorize pair based on data availability"""
        forward_count = len(result["available_forwards"])
        longest = result["longest_tenor"]
        
        if "5Y" in result["available_forwards"] and forward_count >= 10:
            self.categories["full_5y"].append(pair)
        elif "3Y" in result["available_forwards"] and forward_count >= 8:
            self.categories["full_3y"].append(pair)
        elif longest in ["2Y", "3Y", "5Y"]:
            self.categories["partial_long"].append(pair)
        elif forward_count > 0:
            self.categories["partial_short"].append(pair)
        elif result["has_spot"]:
            self.categories["spot_only"].append(pair)
        else:
            self.categories["no_data"].append(pair)
    
    async def analyze_all_pairs(self):
        """Analyze all currency pairs"""
        print("=" * 80)
        print("BLOOMBERG FX FORWARD DATA COVERAGE ANALYSIS")
        print("=" * 80)
        print(f"Analyzing {sum(len(pairs) for pairs in CURRENCY_PAIRS.values())} currency pairs")
        print(f"Checking {len(FORWARD_TENORS)} forward tenors per pair")
        print("=" * 80)
        
        for category, pairs in CURRENCY_PAIRS.items():
            print(f"\n{category} CURRENCIES:")
            print("-" * 40)
            
            for pair in pairs:
                result = await self.analyze_pair(pair, category)
                self.results[pair] = result
                await asyncio.sleep(0.5)  # Rate limiting
        
        self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive report"""
        print("\n" + "=" * 80)
        print("COVERAGE SUMMARY")
        print("=" * 80)
        
        total = len(self.results)
        
        # Print categories
        categories_info = [
            ("Full 5Y Coverage", self.categories["full_5y"], "✅"),
            ("Full 3Y Coverage", self.categories["full_3y"], "✅"),
            ("Partial Long-dated", self.categories["partial_long"], "⚠️"),
            ("Partial Short-dated", self.categories["partial_short"], "⚠️"),
            ("Spot Only", self.categories["spot_only"], "🟡"),
            ("No Data", self.categories["no_data"], "❌")
        ]
        
        for name, pairs, icon in categories_info:
            if pairs:
                pct = len(pairs) / total * 100
                print(f"\n{icon} {name} ({len(pairs)} pairs - {pct:.1f}%):")
                for pair in sorted(pairs):
                    result = self.results[pair]
                    if result.get("longest_tenor"):
                        print(f"   {pair}: up to {result['longest_tenor']}")
                    else:
                        print(f"   {pair}")
        
        # Detailed category analysis
        print("\n" + "=" * 80)
        print("ANALYSIS BY CATEGORY")
        print("=" * 80)
        
        for cat_name, cat_pairs in CURRENCY_PAIRS.items():
            results = [self.results.get(p) for p in cat_pairs if p in self.results]
            with_5y = sum(1 for r in results if "5Y" in r.get("available_forwards", []))
            with_forwards = sum(1 for r in results if r.get("available_forwards"))
            
            print(f"\n{cat_name}:")
            print(f"  Total pairs: {len(cat_pairs)}")
            print(f"  With 5Y data: {with_5y} ({with_5y/len(cat_pairs)*100:.1f}%)")
            print(f"  With any forwards: {with_forwards} ({with_forwards/len(cat_pairs)*100:.1f}%)")
        
        # Special cases
        print("\n" + "=" * 80)
        print("SPECIAL CASES")
        print("=" * 80)
        
        # NDF candidates
        ndf_candidates = []
        for pair in self.categories["spot_only"]:
            if any(curr in pair for curr in ["CNH", "INR", "KRW", "TWD", "IDR", "MYR", "PHP"]):
                ndf_candidates.append(pair)
        
        if ndf_candidates:
            print("\nPotential NDF currencies (spot only):")
            for pair in sorted(ndf_candidates):
                print(f"  - {pair}")
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"forward_coverage_analysis_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_pairs": total,
                    "categories": {k: len(v) for k, v in self.categories.items()}
                },
                "categories": self.categories,
                "detailed_results": self.results
            }, f, indent=2)
        
        print(f"\n📊 Detailed results saved to: {filename}")

async def main():
    analyzer = ForwardDataAnalyzer()
    await analyzer.analyze_all_pairs()

if __name__ == "__main__":
    asyncio.run(main())