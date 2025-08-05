#!/usr/bin/env python3
"""
Test the simplified central ticker endpoint
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from yield_curve_central_ticker_endpoint import yield_curve_router, YieldCurveRequest
import asyncio

async def test_central_ticker_endpoint():
    """Test the simplified endpoint using only ticker_reference"""
    print("=== Testing Central Ticker Endpoint ===\n")
    
    # Test available curves
    print("1. Available curves:")
    try:
        response = await yield_curve_router.routes[0].endpoint()  # get_available_curves
        for curve in response["curves"]:
            print(f"   {curve['currency']} - {curve['curve_name']} ({curve['ticker_count']} tickers)")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test individual currencies
    print("\n2. Individual currency tests:")
    for currency in ["USD", "EUR", "GBP", "JPY", "BRL"]:
        request = YieldCurveRequest(currency=currency)
        try:
            response = await yield_curve_router.routes[1].endpoint(request)  # get_yield_curve_config
            if response.success:
                print(f"\n   {currency}: {response.title}")
                for inst in response.instruments[:3]:  # Show first 3
                    print(f"      {inst.ticker} - {inst.label}")
            else:
                print(f"\n   {currency}: {response.error}")
        except Exception as e:
            print(f"\n   {currency}: Error - {e}")

if __name__ == "__main__":
    asyncio.run(test_central_ticker_endpoint())