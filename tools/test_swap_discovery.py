#!/usr/bin/env python3
"""
Test actual swap discovery functionality with Bloomberg API
"""

import asyncio
import httpx
import json

async def test_swap_discovery():
    """Test swap discovery with real Bloomberg API"""
    
    api_url = "http://20.172.249.92:8080"
    headers = {
        "Authorization": "Bearer test", 
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        print("Testing Bloomberg swap discovery...")
        
        # Test various swap discovery combinations
        search_combinations = [
            {"search_type": "irs", "currency": "USD"},
            {"search_type": "ois", "currency": "USD"},
            {"search_type": "basis_swaps", "currency": "USD"},
            {"search_type": "swap_indices", "currency": "USD"},
            {"search_type": "irs", "currency": "EUR"},
            {"search_type": "ois", "currency": "EUR"},
        ]
        
        for combo in search_combinations:
            try:
                print(f"\n--- Testing {combo['search_type']} for {combo['currency']} ---")
                
                response = await client.post(
                    f"{api_url}/api/bloomberg/ticker-discovery",
                    json=combo,
                    headers=headers
                )
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"Success: {data.get('success', False)}")
                    print(f"Tickers found: {data.get('tickers_found', 0)}")
                    
                    if data.get('tickers'):
                        print("Sample tickers:")
                        for ticker in data['tickers'][:5]:  # Show first 5
                            print(f"  - {ticker}")
                    
                    if data.get('error'):
                        print(f"Error: {data['error']}")
                else:
                    print(f"Error response: {response.text}")
                    
            except Exception as e:
                print(f"Request error: {e}")
        
        # Test with different search patterns
        print("\n" + "="*60)
        print("Testing specific swap ticker patterns...")
        
        # Try pattern-based discovery
        pattern_searches = [
            {"search_type": "pattern", "pattern": "USSW", "currency": "USD"},
            {"search_type": "pattern", "pattern": "EUSW", "currency": "EUR"},  
            {"search_type": "swap", "currency": "USD"},
            {"search_type": "swaps", "currency": "USD"},
        ]
        
        for pattern in pattern_searches:
            try:
                print(f"\n--- Testing pattern: {pattern} ---")
                
                response = await client.post(
                    f"{api_url}/api/bloomberg/ticker-discovery",
                    json=pattern,
                    headers=headers
                )
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"Success: {data.get('success', False)}")
                    print(f"Tickers found: {data.get('tickers_found', 0)}")
                    
                    if data.get('tickers'):
                        print("Sample tickers:")
                        for ticker in data['tickers'][:3]:
                            print(f"  - {ticker}")
                else:
                    print(f"Error response: {response.text}")
                    
            except Exception as e:
                print(f"Request error: {e}")

if __name__ == "__main__":
    asyncio.run(test_swap_discovery())