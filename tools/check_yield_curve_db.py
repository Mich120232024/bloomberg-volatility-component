#!/usr/bin/env python3
"""
Check the yield curve database endpoint locally
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from yield_curve_db_endpoint import yield_curve_router, YieldCurveRequest
import asyncio
import json

async def check_yield_curve_endpoint():
    """Check the yield curve endpoint directly"""
    print("Checking yield curve database endpoint...")
    
    # Check USD curve
    request = YieldCurveRequest(currency="USD")
    try:
        response = await yield_curve_router.routes[1].endpoint(request)  # get_yield_curve_config
        
        print("\nUSD Yield Curve Configuration:")
        print(f"Title: {response.title}")
        print(f"Success: {response.success}")
        print(f"Number of instruments: {len(response.instruments)}")
        
        if response.instruments:
            print("\nFirst 5 instruments:")
            for inst in response.instruments[:5]:
                print(f"  {inst.ticker} - {inst.label} ({inst.years}Y) - {inst.instrumentType}")
        else:
            print("No instruments found")
            
        if response.error:
            print(f"Error: {response.error}")
            
    except Exception as e:
        print(f"Error: {e}")
        
    # Check batch endpoint
    print("\n\nChecking batch endpoint...")
    currencies = ["USD", "EUR", "GBP", "JPY"]
    try:
        response = await yield_curve_router.routes[2].endpoint(currencies)  # get_batch_yield_curves
        
        for currency, data in response.get("curves", {}).items():
            if data.get("success"):
                print(f"\n{currency}: {data.get('title', 'N/A')} - {len(data.get('instruments', []))} instruments")
            else:
                print(f"\n{currency}: Failed - {data.get('error', 'Unknown error')}")
                
    except Exception as e:
        print(f"Batch error: {e}")

if __name__ == "__main__":
    asyncio.run(check_yield_curve_endpoint())