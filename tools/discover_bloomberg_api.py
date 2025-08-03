#!/usr/bin/env python3
"""
Discover actual Bloomberg API endpoints and structure
"""

import asyncio
import httpx
import json

async def discover_bloomberg_endpoints():
    """Discover what endpoints are actually available on the Bloomberg API"""
    
    api_url = "http://20.172.249.92:8080"
    headers = {
        "Authorization": "Bearer test",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        print("Discovering Bloomberg API endpoints...")
        
        # 1. Root endpoint
        try:
            response = await client.get(f"{api_url}/")
            print(f"\nRoot endpoint (GET /):")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print(json.dumps(response.json(), indent=2))
        except Exception as e:
            print(f"Root endpoint error: {e}")
        
        # 2. Health endpoint
        try:
            response = await client.get(f"{api_url}/health")
            print(f"\nHealth endpoint (GET /health):")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print(json.dumps(response.json(), indent=2))
        except Exception as e:
            print(f"Health endpoint error: {e}")
        
        # 3. Reference data endpoint with real swap tickers
        try:
            payload = {
                "securities": ["USSW1 Curncy", "USSW2 Curncy", "USSW5 Curncy"],
                "fields": ["PX_LAST", "PX_BID", "PX_ASK"]
            }
            response = await client.post(
                f"{api_url}/api/bloomberg/reference",
                json=payload,
                headers=headers
            )
            print(f"\nReference endpoint (POST /api/bloomberg/reference):")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print(json.dumps(response.json(), indent=2))
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Reference endpoint error: {e}")
        
        # 4. Check various possible endpoints
        endpoints_to_check = [
            "/api/bloomberg/ticker-discovery",
            "/api/bloomberg/search",
            "/api/bloomberg/explore", 
            "/api/bloomberg/validate-tickers",
            "/api/bloomberg/validate",
            "/api/bloomberg/historical",
            "/api/market-data",
            "/api/fx/rates"
        ]
        
        for endpoint in endpoints_to_check:
            try:
                # Try GET first
                response = await client.get(f"{api_url}{endpoint}")
                if response.status_code != 404:
                    print(f"\nEndpoint {endpoint} (GET):")
                    print(f"Status: {response.status_code}")
                    if response.status_code == 200:
                        print(json.dumps(response.json(), indent=2))
                    else:
                        print(f"Response: {response.text}")
            except Exception as e:
                print(f"GET {endpoint} error: {e}")
            
            try:
                # Try POST with minimal payload
                response = await client.post(
                    f"{api_url}{endpoint}",
                    json={},
                    headers=headers
                )
                if response.status_code != 404:
                    print(f"\nEndpoint {endpoint} (POST):")
                    print(f"Status: {response.status_code}")
                    if response.status_code == 200:
                        print(json.dumps(response.json(), indent=2))
                    else:
                        print(f"Response: {response.text}")
            except Exception as e:
                pass  # Skip POST errors if endpoint doesn't exist

if __name__ == "__main__":
    asyncio.run(discover_bloomberg_endpoints())