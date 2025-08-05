#!/usr/bin/env python3
"""
Validate extracted tickers and find missing EUR/GBP tickers
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

def validate_tickers_batch(tickers):
    """Validate a batch of tickers"""
    try:
        response = requests.post(
            f"{BLOOMBERG_API_URL}/api/bloomberg/reference",
            headers=HEADERS,
            json={
                "securities": tickers,
                "fields": ["SECURITY_NAME", "PX_LAST"]
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            securities = data.get("data", {}).get("securities_data", [])
            
            valid = []
            invalid = []
            
            for sec in securities:
                ticker = sec.get("security")
                if sec.get("success"):
                    valid.append(ticker)
                else:
                    invalid.append(ticker)
            
            return valid, invalid
        
        return [], tickers
            
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return [], tickers

def search_eur_gbp_patterns():
    """Search for EUR and GBP OIS patterns"""
    patterns = {
        'EUR': [
            # ESTR patterns
            'EESWE1M Curncy', 'EESWE2M Curncy', 'EESWE3M Curncy', 'EESWE6M Curncy',
            'EESWE1 Curncy', 'EESWE2 Curncy', 'EESWE3 Curncy', 'EESWE5 Curncy',
            'EESWE7 Curncy', 'EESWE10 Curncy', 'EESWE15 Curncy', 'EESWE20 Curncy',
            'EESWE25 Curncy', 'EESWE30 Curncy',
            # Alternative EUR patterns
            'EUROA Curncy', 'EUROB Curncy', 'EUROC Curncy', 'EUROF Curncy',
            'EURO1 Curncy', 'EURO2 Curncy', 'EURO3 Curncy', 'EURO5 Curncy',
            'EURO10 Curncy', 'EURO15 Curncy', 'EURO20 Curncy', 'EURO30 Curncy'
        ],
        'GBP': [
            # SONIA patterns
            'SONIOA Curncy', 'SONIOB Curncy', 'SONIOC Curncy', 'SONIOF Curncy',
            'SONIO1 Curncy', 'SONIO2 Curncy', 'SONIO3 Curncy', 'SONIO5 Curncy',
            'SONIO7 Curncy', 'SONIO10 Curncy', 'SONIO15 Curncy', 'SONIO20 Curncy',
            'SONIO25 Curncy', 'SONIO30 Curncy',
            # Alternative GBP patterns (already have BPSO)
            'SONIA Index', 'SONIARATE Index'
        ]
    }
    
    found_tickers = {}
    
    for currency, test_patterns in patterns.items():
        print(f"\n🔍 Searching {currency} patterns...")
        
        valid, invalid = validate_tickers_batch(test_patterns)
        
        if valid:
            found_tickers[currency] = valid
            print(f"  ✅ Found {len(valid)} valid tickers:")
            for ticker in valid:
                print(f"     {ticker}")
        else:
            print(f"  ❌ No additional {currency} tickers found")
        
        time.sleep(2)
    
    return found_tickers

def main():
    """Validate existing and find missing tickers"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        # Get current ticker counts
        cursor.execute("""
            SELECT currency_code, COUNT(*)
            FROM ticker_reference
            GROUP BY currency_code
            ORDER BY COUNT(*) DESC
        """)
        
        print("=== CURRENT TICKER COUNTS ===")
        for row in cursor.fetchall():
            print(f"{row[0]}: {row[1]} tickers")
        
        # Validate sample tickers
        print("\n=== VALIDATING SAMPLE TICKERS ===")
        
        for currency in ['USD', 'EUR', 'GBP', 'JPY', 'CHF']:
            cursor.execute("""
                SELECT bloomberg_ticker
                FROM ticker_reference
                WHERE currency_code = %s
                LIMIT 5
            """, (currency,))
            
            sample_tickers = [row[0] for row in cursor.fetchall()]
            
            if sample_tickers:
                print(f"\n{currency} validation:")
                valid, invalid = validate_tickers_batch(sample_tickers)
                print(f"  Valid: {len(valid)}, Invalid: {len(invalid)}")
                if invalid:
                    print(f"  Invalid tickers: {invalid}")
                
                time.sleep(1)
        
        # Search for missing EUR/GBP tickers
        print("\n=== SEARCHING FOR MISSING EUR/GBP TICKERS ===")
        
        new_tickers = search_eur_gbp_patterns()
        
        # Add new tickers to database
        if new_tickers:
            print("\n📊 Adding new tickers to database...")
            
            for currency, tickers in new_tickers.items():
                for ticker in tickers:
                    # Determine instrument type
                    inst_type = 'overnight' if 'Index' in ticker else 'ois'
                    
                    cursor.execute("""
                        INSERT INTO ticker_reference 
                        (bloomberg_ticker, currency_code, instrument_type, curve_name, is_active)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (bloomberg_ticker) DO NOTHING
                    """, (ticker, currency, inst_type, f'{currency}_OIS', True))
            
            conn.commit()
            print("✅ New tickers added")
        
        # Final state
        cursor.execute("""
            SELECT currency_code, COUNT(*)
            FROM ticker_reference
            GROUP BY currency_code
            ORDER BY COUNT(*) DESC
        """)
        
        print("\n=== FINAL TICKER COUNTS ===")
        total = 0
        for row in cursor.fetchall():
            print(f"{row[0]}: {row[1]} tickers")
            total += row[1]
        
        print(f"\n🎉 TOTAL TICKERS: {total}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()