#!/usr/bin/env python3
"""
Complete systematic discovery of ALL swap tickers for ALL currencies
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

# ALL currencies to search
ALL_CURRENCIES = [
    'USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD', 'SEK', 'NOK',
    'MXN', 'ZAR', 'TRY', 'CNH', 'INR', 'KRW', 'TWD', 'SGD', 'HKD', 'THB', 
    'ILS', 'PLN', 'CZK', 'HUF', 'RUB', 'PHP', 'DKK', 'BRL'
]

# Swap types to discover
SWAP_TYPES = ['ois', 'irs', 'basis_swaps', 'swap_indices']

def discover_tickers(search_type, currency):
    """Discover tickers for a specific type and currency"""
    try:
        response = requests.post(
            f"{BLOOMBERG_API_URL}/api/bloomberg/ticker-discovery",
            headers=HEADERS,
            json={
                "search_type": search_type,
                "currency": currency,
                "max_results": 100
            },
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("tickers", [])
        else:
            print(f"❌ {currency} {search_type}: HTTP {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ {currency} {search_type}: {str(e)}")
        return []

def validate_tickers(tickers):
    """Validate a batch of tickers"""
    if not tickers:
        return []
    
    try:
        response = requests.post(
            f"{BLOOMBERG_API_URL}/api/bloomberg/validate-tickers",
            headers=HEADERS,
            json=tickers[:50],  # Limit batch size
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("valid_tickers", [])
        else:
            print(f"❌ Validation failed: HTTP {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Validation error: {str(e)}")
        return []

def populate_database(discoveries):
    """Populate database with discovered tickers"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        # Clear existing data
        cursor.execute("DELETE FROM ticker_reference")
        print(f"Cleared existing ticker_reference data")
        
        total_added = 0
        
        for currency in discoveries:
            for swap_type in discoveries[currency]:
                tickers = discoveries[currency][swap_type]
                
                for ticker_data in tickers:
                    ticker = ticker_data.get('ticker', '')
                    if ticker:
                        cursor.execute("""
                            INSERT INTO ticker_reference 
                            (bloomberg_ticker, currency_code, instrument_type, curve_name, is_active)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (bloomberg_ticker) DO NOTHING
                        """, (
                            ticker, 
                            currency, 
                            swap_type, 
                            f"{currency}_{swap_type.upper()}", 
                            True
                        ))
                        total_added += 1
        
        conn.commit()
        print(f"✅ Added {total_added} tickers to database")
        
        # Show final counts
        cursor.execute("""
            SELECT currency_code, instrument_type, COUNT(*) 
            FROM ticker_reference 
            GROUP BY currency_code, instrument_type 
            ORDER BY currency_code, instrument_type
        """)
        
        print("\n=== FINAL DATABASE COUNTS ===")
        for row in cursor.fetchall():
            print(f"{row[0]} {row[1]}: {row[2]} tickers")
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        conn.rollback()
    finally:
        conn.close()

def main():
    """Complete systematic discovery"""
    print("=== COMPLETE SWAP DISCOVERY FOR ALL CURRENCIES ===")
    
    all_discoveries = {}
    total_found = 0
    
    for currency in ALL_CURRENCIES:
        print(f"\n🔍 {currency}:")
        currency_discoveries = {}
        
        for swap_type in SWAP_TYPES:
            print(f"  Discovering {swap_type}...")
            
            # Discover tickers
            discovered = discover_tickers(swap_type, currency)
            time.sleep(1)  # Rate limiting
            
            if discovered:
                # Extract just ticker names for validation
                ticker_names = [t.get('ticker', '') for t in discovered if t.get('ticker')]
                
                if ticker_names:
                    print(f"    Found {len(ticker_names)} potential tickers, validating...")
                    
                    # Validate tickers
                    valid_tickers = validate_tickers(ticker_names)
                    time.sleep(2)  # Rate limiting
                    
                    if valid_tickers:
                        # Match back to full data
                        valid_full_data = []
                        for ticker in valid_tickers:
                            for orig in discovered:
                                if orig.get('ticker') == ticker:
                                    valid_full_data.append(orig)
                                    break
                        
                        currency_discoveries[swap_type] = valid_full_data
                        print(f"    ✅ {len(valid_tickers)} valid {swap_type} tickers")
                        total_found += len(valid_tickers)
                    else:
                        print(f"    ❌ No valid {swap_type} tickers")
                else:
                    print(f"    ❌ No {swap_type} tickers found")
            else:
                print(f"    ❌ No {swap_type} discovery results")
        
        if currency_discoveries:
            all_discoveries[currency] = currency_discoveries
    
    # Save discoveries
    with open('complete_swap_discoveries.json', 'w') as f:
        json.dump(all_discoveries, f, indent=2)
    
    print(f"\n=== DISCOVERY COMPLETE ===")
    print(f"Total valid tickers found: {total_found}")
    print(f"Currencies with data: {len(all_discoveries)}")
    
    # Populate database
    if all_discoveries:
        print("\n🔄 Populating database...")
        populate_database(all_discoveries)
    
    print("\n✅ COMPLETE SWAP DISCOVERY FINISHED")

if __name__ == "__main__":
    main()