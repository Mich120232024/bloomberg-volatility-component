#!/usr/bin/env python3
"""
Quick test of Bloomberg API connectivity and ticker discovery functionality
"""

import asyncio
import httpx
import json

async def test_bloomberg_api():
    """Test Bloomberg API connection and ticker discovery"""
    
    api_url = "http://20.172.249.92:8080"
    headers = {
        "Authorization": "Bearer test",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # 1. Test health check
        print("Testing Bloomberg API health...")
        try:
            response = await client.get(f"{api_url}/health")
            print(f"Health check: {response.status_code}")
            if response.status_code == 200:
                print("✓ Bloomberg API is healthy")
            else:
                print("✗ Bloomberg API health check failed")
                return
        except Exception as e:
            print(f"✗ Bloomberg API connection failed: {e}")
            return
        
        # 2. Test ticker discovery for USD IRS
        print("\nTesting ticker discovery for USD Interest Rate Swaps...")
        try:
            payload = {
                "search_type": "irs",
                "currency": "USD", 
                "max_results": 10
            }
            
            response = await client.post(
                f"{api_url}/api/bloomberg/ticker-discovery",
                json=payload,
                headers=headers
            )
            
            print(f"Discovery response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Discovery successful. Found: {json.dumps(data, indent=2)}")
            else:
                print(f"✗ Discovery failed: {response.text}")
                return
        except Exception as e:
            print(f"✗ Discovery test failed: {e}")
            return
        
        # 3. Test ticker validation
        print("\nTesting ticker validation...")
        try:
            test_tickers = ["USSW1 Curncy", "USSW2 Curncy", "INVALID_TICKER"]
            
            response = await client.post(
                f"{api_url}/api/bloomberg/validate-tickers",
                json=test_tickers,
                headers=headers
            )
            
            print(f"Validation response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Validation successful. Results: {json.dumps(data, indent=2)}")
            else:
                print(f"✗ Validation failed: {response.text}")
        except Exception as e:
            print(f"✗ Validation test failed: {e}")
        
        print("\n" + "="*60)
        print("Bloomberg API testing complete!")

if __name__ == "__main__":
    asyncio.run(test_bloomberg_api())