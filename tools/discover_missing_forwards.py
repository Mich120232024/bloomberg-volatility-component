#!/usr/bin/env python3
"""
Discover alternative forward tickers (NDFs, etc.) for currencies with limited coverage
Uses Bloomberg ticker discovery endpoint
"""

import httpx
import asyncio
import json
from datetime import datetime
from typing import Dict, List

# Bloomberg API endpoint
BLOOMBERG_API_URL = "http://20.172.249.92:8080"
API_KEY = "test"

# Currencies needing alternative tickers
MISSING_FORWARDS = {
    "spot_only": {
        "USDINR": "Indian Rupee - NDF likely",
        "USDTWD": "Taiwan Dollar - NDF likely", 
        "USDIDR": "Indonesian Rupiah - NDF likely",
        "USDBRL": "Brazilian Real",
        "USDCLP": "Chilean Peso",
        "USDPEN": "Peruvian Sol",
        "USDARS": "Argentine Peso"
    },
    "limited_coverage": {
        "USDKRW": "Korean Won - only up to 9M",
        "USDPHP": "Philippine Peso - only up to 9M",
        "USDMYR": "Malaysian Ringgit - only up to 9M"
    }
}

class NDFDiscoverer:
    def __init__(self):
        self.discoveries = {}
        self.headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
    async def discover_ndf_tickers(self, currency: str, pair: str):
        """Try to discover NDF tickers for a currency"""
        print(f"\n{'='*60}")
        print(f"Discovering tickers for {pair} ({currency})")
        print('='*60)
        
        results = []
        
        # Try different search patterns
        search_patterns = [
            {"search_type": "ndf", "currency": currency},
            {"search_type": "fx_forward", "currency": currency},
            {"search_type": "fx", "currency": currency, "instrument_type": "ndf"},
            {"search_pattern": f"{currency}*NDF*", "max_results": 20},
            {"search_pattern": f"NDF*{currency}*", "max_results": 20},
            {"search_pattern": f"{pair}*NDF*", "max_results": 20}
        ]
        
        for pattern in search_patterns:
            result = await self.search_tickers(pattern, pair)
            if result:
                results.extend(result)
        
        # Also try validation of common NDF patterns
        validation_tickers = self.generate_ndf_patterns(pair, currency)
        validated = await self.validate_tickers(validation_tickers, pair)
        if validated:
            results.extend(validated)
        
        return results
    
    def generate_ndf_patterns(self, pair: str, currency: str) -> List[str]:
        """Generate common NDF ticker patterns to validate"""
        patterns = []
        tenors = ["1W", "2W", "1M", "2M", "3M", "6M", "9M", "1Y", "2Y", "3Y", "5Y"]
        
        # Common NDF patterns
        for tenor in tenors:
            patterns.extend([
                f"{pair}N{tenor} Curncy",      # USDINRN1M
                f"{pair}{tenor}N Curncy",       # USDINR1MN
                f"NDF{pair}{tenor} Curncy",    # NDFUSDINR1M
                f"{pair}{tenor} NDF Curncy",   # USDINR1M NDF
                f"{currency}NDF{tenor} Curncy", # INRNDF1M
                f"USD{currency}N{tenor} Curncy" # USDINRN1M
            ])
        
        return patterns
    
    async def search_tickers(self, search_params: Dict, pair: str) -> List[str]:
        """Search for tickers using discovery endpoint"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                print(f"\nSearching with params: {search_params}")
                
                response = await client.post(
                    f"{BLOOMBERG_API_URL}/api/bloomberg/ticker-discovery",
                    json=search_params,
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") and data.get("tickers"):
                        found_tickers = []
                        for ticker_info in data["tickers"]:
                            ticker = ticker_info.get("ticker", "")
                            desc = ticker_info.get("description", "")
                            if any(keyword in ticker.upper() for keyword in ["NDF", "NON", "DELIVER"]) or \
                               any(keyword in desc.upper() for keyword in ["NDF", "NON-DELIVERABLE", "FORWARD"]):
                                found_tickers.append(ticker)
                                print(f"  ✓ Found: {ticker} - {desc}")
                        return found_tickers
                    else:
                        print(f"  No results")
                else:
                    print(f"  API error: {response.status_code}")
        except Exception as e:
            print(f"  Exception: {str(e)}")
        
        return []
    
    async def validate_tickers(self, tickers: List[str], pair: str) -> List[str]:
        """Validate a list of potential tickers"""
        if not tickers:
            return []
            
        print(f"\nValidating {len(tickers)} potential ticker patterns...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Batch validate in chunks of 20
                valid_tickers = []
                
                for i in range(0, len(tickers), 20):
                    batch = tickers[i:i+20]
                    
                    response = await client.post(
                        f"{BLOOMBERG_API_URL}/api/bloomberg/validate-tickers",
                        json=batch,
                        headers=self.headers
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("success") and data.get("results"):
                            for result in data["results"]:
                                if result.get("valid") and result.get("data"):
                                    ticker = result["ticker"]
                                    px_last = result["data"].get("PX_LAST")
                                    name = result["data"].get("NAME", "")
                                    if px_last is not None:
                                        valid_tickers.append(ticker)
                                        print(f"  ✓ Valid: {ticker} = {px_last} ({name})")
                
                return valid_tickers
                
        except Exception as e:
            print(f"  Validation error: {str(e)}")
        
        return []
    
    async def discover_all(self):
        """Discover alternative tickers for all currencies needing them"""
        print("BLOOMBERG NDF/ALTERNATIVE FORWARD TICKER DISCOVERY")
        print("="*80)
        
        # Process spot-only currencies
        print("\nCURRENCIES WITH NO FORWARD DATA:")
        for pair, desc in MISSING_FORWARDS["spot_only"].items():
            currency = pair.replace("USD", "")
            results = await self.discover_ndf_tickers(currency, pair)
            self.discoveries[pair] = {
                "description": desc,
                "type": "spot_only",
                "discovered_tickers": results
            }
            await asyncio.sleep(1)  # Rate limiting
        
        # Process limited coverage currencies
        print("\n\nCURRENCIES WITH LIMITED FORWARD COVERAGE:")
        for pair, desc in MISSING_FORWARDS["limited_coverage"].items():
            currency = pair.replace("USD", "")
            results = await self.discover_ndf_tickers(currency, pair)
            self.discoveries[pair] = {
                "description": desc,
                "type": "limited_coverage",
                "discovered_tickers": results
            }
            await asyncio.sleep(1)  # Rate limiting
        
        # Generate report
        self.generate_report()
    
    def generate_report(self):
        """Generate discovery report"""
        print("\n" + "="*80)
        print("DISCOVERY SUMMARY")
        print("="*80)
        
        successful = []
        failed = []
        
        for pair, data in self.discoveries.items():
            if data["discovered_tickers"]:
                successful.append(pair)
            else:
                failed.append(pair)
        
        print(f"\n✅ DISCOVERED ALTERNATIVE TICKERS ({len(successful)} currencies):")
        for pair in successful:
            data = self.discoveries[pair]
            print(f"\n{pair} ({data['description']}):")
            for ticker in data["discovered_tickers"]:
                print(f"  - {ticker}")
        
        print(f"\n❌ NO ALTERNATIVES FOUND ({len(failed)} currencies):")
        for pair in failed:
            data = self.discoveries[pair]
            print(f"  - {pair} ({data['description']})")
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"ndf_discovery_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "discoveries": self.discoveries,
                "summary": {
                    "successful": successful,
                    "failed": failed
                }
            }, f, indent=2)
        
        print(f"\n📊 Results saved to: {filename}")

async def main():
    discoverer = NDFDiscoverer()
    await discoverer.discover_all()

if __name__ == "__main__":
    asyncio.run(main())