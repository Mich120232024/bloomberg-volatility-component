#!/usr/bin/env python3
"""
Find and validate Nordic OIS tickers
"""

import requests
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

def test_nordic_patterns():
    """Test various Nordic OIS patterns"""
    patterns = {
        'SEK': [
            # STIBOR patterns
            'STIBOR ON Index', 'SEONIA Index', 'SWESTR Index',
            'SKSOA Curncy', 'SKSOB Curncy', 'SKSOC Curncy', 'SKSOF Curncy',
            'SKSO1 Curncy', 'SKSO2 Curncy', 'SKSO3 Curncy', 'SKSO5 Curncy',
            'SKSO7 Curncy', 'SKSO10 Curncy', 'SKSO15 Curncy', 'SKSO20 Curncy',
            'SKSO30 Curncy'
        ],
        'NOK': [
            # NOWA patterns
            'NOWA Index', 'NIBOR ON Index', 'NOONIA Index',
            'NKSOA Curncy', 'NKSOB Curncy', 'NKSOC Curncy', 'NKSOF Curncy',
            'NKSO1 Curncy', 'NKSO2 Curncy', 'NKSO3 Curncy', 'NKSO5 Curncy',
            'NKSO7 Curncy', 'NKSO10 Curncy', 'NKSO15 Curncy', 'NKSO20 Curncy',
            'NKSO30 Curncy'
        ]
    }
    
    found_tickers = {}
    
    for currency, test_patterns in patterns.items():
        print(f"\n🔍 Testing {currency} patterns...")
        
        # Test in batches
        for i in range(0, len(test_patterns), 5):
            batch = test_patterns[i:i+5]
            
            try:
                response = requests.post(
                    f"{BLOOMBERG_API_URL}/api/bloomberg/reference",
                    headers=HEADERS,
                    json={
                        "securities": batch,
                        "fields": ["SECURITY_NAME", "PX_LAST"]
                    },
                    timeout=15
                )
                
                if response.status_code == 200:
                    data = response.json()
                    securities = data.get("data", {}).get("securities_data", [])
                    
                    for sec in securities:
                        if sec.get("success"):
                            ticker = sec.get("security")
                            name = sec.get("fields", {}).get("SECURITY_NAME", "")
                            
                            if currency not in found_tickers:
                                found_tickers[currency] = []
                            
                            found_tickers[currency].append({
                                'ticker': ticker,
                                'name': name
                            })
                            print(f"  ✅ {ticker} - {name}")
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
    
    return found_tickers

def main():
    """Find and add Nordic OIS tickers"""
    print("=== FINDING NORDIC OIS TICKERS ===")
    
    # Test patterns
    found = test_nordic_patterns()
    
    if found:
        print("\n📊 Adding to database...")
        
        conn = get_database_connection()
        cursor = conn.cursor()
        
        try:
            added = 0
            
            for currency, tickers in found.items():
                for ticker_data in tickers:
                    ticker = ticker_data['ticker']
                    
                    # Determine instrument type
                    inst_type = 'overnight' if 'Index' in ticker else 'ois'
                    
                    cursor.execute("""
                        INSERT INTO ticker_reference 
                        (bloomberg_ticker, currency_code, instrument_type, curve_name, is_active)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (bloomberg_ticker) DO NOTHING
                    """, (ticker, currency, inst_type, f'{currency}_OIS', True))
                    
                    if cursor.rowcount > 0:
                        added += 1
            
            conn.commit()
            print(f"✅ Added {added} new tickers")
            
            # Show final G10 coverage
            cursor.execute("""
                SELECT currency_code, COUNT(*)
                FROM ticker_reference
                WHERE currency_code IN ('USD','EUR','GBP','JPY','CHF','CAD','AUD','NZD','SEK','NOK')
                GROUP BY currency_code
                ORDER BY currency_code
            """)
            
            print("\n=== G10 COVERAGE ===")
            for row in cursor.fetchall():
                print(f"{row[0]}: {row[1]} tickers")
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            conn.rollback()
        finally:
            conn.close()
    else:
        print("\n❌ No Nordic OIS tickers found")

if __name__ == "__main__":
    main()