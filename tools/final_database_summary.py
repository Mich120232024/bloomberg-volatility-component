#!/usr/bin/env python3
"""
Generate comprehensive summary of populated database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from yield_curve_db_endpoint import get_database_connection
import json

def main():
    """Generate comprehensive database summary"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        # Get all tickers by currency with details
        cursor.execute("""
            SELECT 
                currency_code,
                bloomberg_ticker,
                instrument_type,
                curve_name
            FROM ticker_reference
            ORDER BY currency_code, 
                     CASE instrument_type 
                         WHEN 'overnight' THEN 1 
                         ELSE 2 
                     END,
                     bloomberg_ticker
        """)
        
        all_data = {}
        for row in cursor.fetchall():
            currency = row[0]
            if currency not in all_data:
                all_data[currency] = {
                    'tickers': [],
                    'overnight': [],
                    'ois': [],
                    'curve_name': row[3]
                }
            
            ticker_info = {
                'ticker': row[1],
                'type': row[2]
            }
            
            all_data[currency]['tickers'].append(ticker_info)
            
            if row[2] == 'overnight':
                all_data[currency]['overnight'].append(row[1])
            else:
                all_data[currency]['ois'].append(row[1])
        
        # Generate report
        print("="*80)
        print("COMPLETE OIS DATABASE POPULATION REPORT")
        print("="*80)
        
        # Summary statistics
        total_tickers = sum(len(data['tickers']) for data in all_data.values())
        currencies_with_ois = len(all_data)
        g10_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD', 'SEK', 'NOK']
        g10_coverage = [c for c in g10_currencies if c in all_data]
        
        print(f"\n📊 SUMMARY STATISTICS:")
        print(f"  Total OIS tickers: {total_tickers}")
        print(f"  Currencies covered: {currencies_with_ois}")
        print(f"  G10 coverage: {len(g10_coverage)}/10 ({', '.join(g10_coverage)})")
        
        # Missing G10
        missing_g10 = [c for c in g10_currencies if c not in all_data]
        if missing_g10:
            print(f"  Missing G10: {', '.join(missing_g10)}")
        
        # Detailed by currency
        print(f"\n📈 DETAILED COVERAGE BY CURRENCY:")
        print(f"{'Currency':<10} {'Total':<8} {'Overnight':<12} {'OIS Tickers':<10} {'Curve Name'}")
        print("-"*70)
        
        for currency in sorted(all_data.keys(), key=lambda x: len(all_data[x]['tickers']), reverse=True):
            data = all_data[currency]
            total = len(data['tickers'])
            overnight = len(data['overnight'])
            ois = len(data['ois'])
            curve = data['curve_name']
            
            print(f"{currency:<10} {total:<8} {overnight:<12} {ois:<10} {curve}")
        
        # Save detailed JSON
        summary = {
            'total_tickers': total_tickers,
            'currencies_covered': currencies_with_ois,
            'g10_coverage': f"{len(g10_coverage)}/10",
            'currencies': {}
        }
        
        for currency, data in all_data.items():
            summary['currencies'][currency] = {
                'total': len(data['tickers']),
                'overnight_tickers': data['overnight'],
                'ois_tickers': data['ois'][:10],  # First 10 for brevity
                'curve_name': data['curve_name']
            }
        
        with open('final_ois_database_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n✅ Summary saved to final_ois_database_summary.json")
        
        # Check tenor coverage for major currencies
        print(f"\n🎯 TENOR COVERAGE CHECK:")
        
        for currency in ['USD', 'EUR', 'GBP', 'JPY', 'CHF']:
            if currency not in all_data:
                print(f"\n{currency}: NO DATA")
                continue
                
            tickers = all_data[currency]['ois']
            
            # Extract tenors
            tenors = []
            for ticker in tickers:
                # Try to extract tenor from ticker name
                if 'A' <= ticker[-8] <= 'K' and 'Curncy' in ticker:
                    # Monthly pattern (USSOA, USSOB, etc.)
                    month = ord(ticker[-8]) - ord('A') + 1
                    tenors.append(f"{month}M")
                elif ticker[-8:-6].isdigit():
                    # Yearly pattern (USSO1, USSO10, etc.)
                    year = ticker.split('O')[-1].split()[0]
                    if 'M' in year:
                        tenors.append(year)
                    else:
                        tenors.append(f"{year}Y")
            
            print(f"\n{currency}: {len(tickers)} OIS tickers")
            print(f"  Tenors: {', '.join(sorted(set(tenors), key=lambda x: (len(x), x)))}")
        
        print(f"\n{'='*80}")
        print("POPULATION COMPLETE - DATABASE READY FOR YIELD CURVE CONSTRUCTION")
        print(f"{'='*80}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()