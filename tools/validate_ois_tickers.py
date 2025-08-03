#!/usr/bin/env python3
"""
Validate OIS tickers one by one using Bloomberg API
"""

import requests
import json
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from yield_curve_db_endpoint import get_database_connection

BLOOMBERG_API_URL = "http://20.172.249.92:8080"
HEADERS = {
    "Authorization": "Bearer test", 
    "Content-Type": "application/json"
}

# USD OIS ticker patterns to validate
USD_TICKERS = [
    # Overnight
    ('SOFRRATE Index', 'O/N', 1),
    
    # Short term 
    ('USSW1Z Curncy', '1D', 1),
    ('USSW1 Curncy', '1W', 7),
    ('USSW2 Curncy', '2W', 14),
    ('USSW3 Curncy', '3W', 21),
    
    # Monthly
    ('USSOA Curncy', '1M', 30),
    ('USSOB Curncy', '2M', 60),
    ('USSOC Curncy', '3M', 90),
    ('USSOD Curncy', '4M', 120),
    ('USSOE Curncy', '5M', 150),
    ('USSOF Curncy', '6M', 180),
    ('USSOG Curncy', '7M', 210),
    ('USSOH Curncy', '8M', 240),
    ('USSOI Curncy', '9M', 270),
    ('USSOJ Curncy', '10M', 300),
    ('USSOK Curncy', '11M', 330),
    
    # Yearly
    ('USSO1 Curncy', '1Y', 365),
    ('USSO15M Curncy', '15M', 456),
    ('USSO18M Curncy', '18M', 548),
    ('USSO21M Curncy', '21M', 639),
    ('USSO2 Curncy', '2Y', 730),
    ('USSO3 Curncy', '3Y', 1095),
    ('USSO4 Curncy', '4Y', 1460),
    ('USSO5 Curncy', '5Y', 1825),
    ('USSO6 Curncy', '6Y', 2190),
    ('USSO7 Curncy', '7Y', 2555),
    ('USSO8 Curncy', '8Y', 2920),
    ('USSO9 Curncy', '9Y', 3285),
    ('USSO10 Curncy', '10Y', 3650),
    ('USSO12 Curncy', '12Y', 4380),
    ('USSO15 Curncy', '15Y', 5475),
    ('USSO20 Curncy', '20Y', 7300),
    ('USSO25 Curncy', '25Y', 9125),
    ('USSO30 Curncy', '30Y', 10950),
    ('USSO40 Curncy', '40Y', 14600),
    ('USSO50 Curncy', '50Y', 18250)
]

def validate_ticker(ticker):
    """Check if ticker returns real data from Bloomberg"""
    try:
        response = requests.post(
            f"{BLOOMBERG_API_URL}/api/bloomberg/reference",
            headers=HEADERS,
            json={
                "securities": [ticker],
                "fields": ["PX_LAST", "SECURITY_NAME", "CRNCY"]
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            securities_data = data.get("data", {}).get("securities_data", [])
            if securities_data and securities_data[0].get("success"):
                return True, securities_data[0].get("fields", {})
            else:
                return False, "No data"
        else:
            return False, f"HTTP {response.status_code}"
            
    except Exception as e:
        return False, str(e)

def main():
    """Validate all tickers"""
    valid_tickers = []
    
    print("=== VALIDATING USD OIS TICKERS ===\n")
    
    for ticker, tenor, days in USD_TICKERS:
        valid, result = validate_ticker(ticker)
        
        if valid:
            price = result.get('PX_LAST', 'N/A')
            name = result.get('SECURITY_NAME', 'N/A')
            print(f"✅ {ticker:<20} | {tenor:<4} | {days:>5}d | {price} | {name}")
            valid_tickers.append({
                'ticker': ticker,
                'tenor': tenor,
                'days': days,
                'price': price,
                'name': name
            })
        else:
            print(f"❌ {ticker:<20} | {tenor:<4} | {result}")
        
        time.sleep(0.5)  # Rate limiting
    
    print(f"\n=== SUMMARY ===")
    print(f"Valid: {len(valid_tickers)} tickers")
    
    # Save valid tickers
    if valid_tickers:
        with open('validated_usd_ois.json', 'w') as f:
            json.dump(valid_tickers, f, indent=2)
        
        print("\nPopulating ticker_reference...")
        conn = get_database_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM ticker_reference WHERE currency_code = 'USD'")
            
            for t in valid_tickers:
                cursor.execute("""
                    INSERT INTO ticker_reference 
                    (bloomberg_ticker, currency_code, instrument_type, curve_name, is_active)
                    VALUES (%s, %s, %s, %s, %s)
                """, (t['ticker'], 'USD', 'ois', 'USD_SOFR_OIS', True))
            
            conn.commit()
            print(f"Added {len(valid_tickers)} USD tickers")
            
        except Exception as e:
            print(f"Database error: {e}")
            conn.rollback()
        finally:
            conn.close()

if __name__ == "__main__":
    main()