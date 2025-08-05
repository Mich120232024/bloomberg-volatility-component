#!/usr/bin/env python3
"""
Check complete coverage and identify gaps
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from yield_curve_db_endpoint import get_database_connection

def main():
    conn = get_database_connection()
    cursor = conn.cursor()
    
    # Get all tickers with proper mapping
    cursor.execute("""
        SELECT currency_code, bloomberg_ticker
        FROM ticker_reference
        WHERE instrument_type = 'ois'
        ORDER BY currency_code, bloomberg_ticker
    """)
    
    print("=== COMPLETE COVERAGE ANALYSIS ===")
    
    # Target currencies from user's FX pairs
    target_g10 = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD', 'SEK', 'NOK']
    target_em = ['MXN', 'ZAR', 'TRY', 'CNH', 'INR', 'KRW', 'TWD', 'SGD', 'HKD', 'THB', 
                 'ILS', 'PLN', 'CZK', 'HUF', 'RUB', 'PHP', 'DKK', 'BRL']
    
    # Target tenors
    target_tenors = ['1M', '2M', '3M', '6M', '9M', '12M', '15M', '18M', '21M', 
                     '2Y', '3Y', '4Y', '5Y', '7Y', '10Y', '15Y', '20Y', '25Y', '30Y']
    
    # Organize by currency
    by_currency = {}
    for currency, ticker in cursor.fetchall():
        if currency not in by_currency:
            by_currency[currency] = []
        by_currency[currency].append(ticker)
    
    # Analyze coverage
    print(f"\nTARGET: {len(target_g10)} G10 + {len(target_em)} EM = {len(target_g10) + len(target_em)} currencies")
    print(f"HAVE: {len(by_currency)} currencies in database")
    
    # G10 coverage
    print("\n=== G10 COVERAGE ===")
    g10_covered = []
    for currency in target_g10:
        if currency in by_currency:
            g10_covered.append(currency)
            print(f"✅ {currency}: {len(by_currency[currency])} tickers")
        else:
            print(f"❌ {currency}: MISSING")
    
    # EM coverage  
    print("\n=== EM COVERAGE ===")
    em_covered = []
    for currency in target_em:
        if currency in by_currency:
            em_covered.append(currency)
            print(f"✅ {currency}: {len(by_currency[currency])} tickers")
        else:
            print(f"❌ {currency}: NO OIS MARKET")
    
    # Summary
    print(f"\n=== SUMMARY ===")
    print(f"G10 Coverage: {len(g10_covered)}/{len(target_g10)} ({len(g10_covered)/len(target_g10)*100:.0f}%)")
    print(f"EM Coverage: {len(em_covered)}/{len(target_em)} ({len(em_covered)/len(target_em)*100:.0f}%)")
    print(f"Total: {len(g10_covered) + len(em_covered)}/{len(target_g10) + len(target_em)} ({(len(g10_covered) + len(em_covered))/(len(target_g10) + len(target_em))*100:.0f}%)")
    
    # Missing critical G10
    missing_g10 = set(target_g10) - set(g10_covered)
    if missing_g10:
        print(f"\n⚠️ MISSING CRITICAL G10: {sorted(missing_g10)}")
        print("These MUST be added for complete implementation")
    
    conn.close()

if __name__ == "__main__":
    main()