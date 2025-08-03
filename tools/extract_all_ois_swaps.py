#!/usr/bin/env python3
"""
Extract ALL OIS and swap tickers from bloomberg_tickers
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from yield_curve_db_endpoint import get_database_connection

def main():
    """Extract and populate all OIS/swap tickers"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        # Find ALL OIS/swap related tickers
        cursor.execute("""
            SELECT currency_code, bloomberg_ticker, tenor, description, instrument_type
            FROM bloomberg_tickers
            WHERE (
                bloomberg_ticker LIKE '%SO%' 
                OR bloomberg_ticker LIKE '%OIS%'
                OR bloomberg_ticker LIKE '%RATE Index'
                OR bloomberg_ticker LIKE '%ON Index'
                OR bloomberg_ticker LIKE '%SONIA%'
                OR bloomberg_ticker LIKE '%SOFR%'
                OR bloomberg_ticker LIKE '%ESTR%'
                OR bloomberg_ticker LIKE '%TONAR%'
                OR bloomberg_ticker LIKE '%SARON%'
                OR bloomberg_ticker LIKE '%CORRA%'
                OR bloomberg_ticker LIKE '%AONIA%'
                OR bloomberg_ticker LIKE '%NOWA%'
                OR bloomberg_ticker LIKE '%STIBOR%'
                OR bloomberg_ticker LIKE '%SWESTR%'
                OR bloomberg_ticker LIKE '%SELIC%'
                OR description ILIKE '%overnight%'
                OR description ILIKE '%OIS%'
                OR description ILIKE '%swap%curve%'
            )
            AND currency_code IN ('USD','EUR','GBP','JPY','CHF','CAD','AUD','NZD','SEK','NOK','BRL',
                                  'MXN','ZAR','TRY','CNH','INR','KRW','TWD','SGD','HKD','THB',
                                  'ILS','PLN','CZK','HUF','RUB','PHP','DKK')
            AND bloomberg_ticker NOT LIKE '%/%'  -- Exclude FX pairs
            ORDER BY currency_code, tenor_numeric
        """)
        
        all_tickers = cursor.fetchall()
        print(f"Found {len(all_tickers)} potential OIS/swap tickers")
        
        # Clear ticker_reference
        cursor.execute("DELETE FROM ticker_reference")
        print("Cleared ticker_reference table")
        
        # Group by currency and insert
        by_currency = {}
        for row in all_tickers:
            currency = row[0]
            if currency not in by_currency:
                by_currency[currency] = []
            by_currency[currency].append(row)
        
        # Insert all tickers
        total_inserted = 0
        for currency, tickers in sorted(by_currency.items()):
            print(f"\n{currency}: {len(tickers)} tickers")
            
            for ticker_data in tickers:
                bloomberg_ticker = ticker_data[1]
                
                # Determine instrument type
                if 'Index' in bloomberg_ticker and ('RATE' in bloomberg_ticker or 'ON' in bloomberg_ticker):
                    inst_type = 'overnight'
                else:
                    inst_type = 'ois'
                
                # Determine curve name
                curve_name = f"{currency}_OIS"
                
                cursor.execute("""
                    INSERT INTO ticker_reference 
                    (bloomberg_ticker, currency_code, instrument_type, curve_name, is_active)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (bloomberg_ticker) DO NOTHING
                """, (bloomberg_ticker, currency, inst_type, curve_name, True))
                
                if cursor.rowcount > 0:
                    total_inserted += 1
                    print(f"  {bloomberg_ticker} - {ticker_data[2]}")
        
        conn.commit()
        print(f"\n✅ Successfully inserted {total_inserted} tickers")
        
        # Show final summary
        cursor.execute("""
            SELECT currency_code, COUNT(*), string_agg(DISTINCT instrument_type, ', ')
            FROM ticker_reference
            GROUP BY currency_code
            ORDER BY COUNT(*) DESC
        """)
        
        print("\n=== FINAL DATABASE STATE ===")
        grand_total = 0
        for row in cursor.fetchall():
            print(f"{row[0]}: {row[1]} tickers ({row[2]})")
            grand_total += row[1]
        
        print(f"\n🎉 TOTAL TICKERS IN DATABASE: {grand_total}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()