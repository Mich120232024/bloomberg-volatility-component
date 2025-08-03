#!/usr/bin/env python3
"""
Populate ticker_reference from existing bloomberg_tickers table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from yield_curve_db_endpoint import get_database_connection

def main():
    """Populate ticker_reference from bloomberg_tickers"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        # Clear ticker_reference for fresh start
        cursor.execute("DELETE FROM ticker_reference")
        print(f"Cleared ticker_reference table")
        
        # Copy ALL OIS and overnight tickers from bloomberg_tickers
        cursor.execute("""
            INSERT INTO ticker_reference (bloomberg_ticker, currency_code, instrument_type, curve_name, is_active)
            SELECT DISTINCT
                bloomberg_ticker,
                currency_code,
                LOWER(instrument_type) as instrument_type,
                COALESCE(curve_name, currency_code || '_OIS') as curve_name,
                is_active
            FROM bloomberg_tickers
            WHERE UPPER(instrument_type) IN ('OIS', 'RATE', 'OVERNIGHT')
            OR bloomberg_ticker LIKE '%SOFR%'
            OR bloomberg_ticker LIKE '%ESTR%' 
            OR bloomberg_ticker LIKE '%SONIA%'
            OR bloomberg_ticker LIKE '%TONAR%'
            OR bloomberg_ticker LIKE '%SARON%'
            OR bloomberg_ticker LIKE '%CORRA%'
            OR bloomberg_ticker LIKE '%AONIA%'
            OR bloomberg_ticker LIKE '%NOWA%'
            OR bloomberg_ticker LIKE '%OCR%'
            OR bloomberg_ticker LIKE '%SELIC%'
            OR bloomberg_ticker LIKE '%STIBOR%'
            OR bloomberg_ticker LIKE '%SWESTR%'
            ON CONFLICT (bloomberg_ticker) DO NOTHING
        """)
        
        added = cursor.rowcount
        print(f"✅ Added {added} tickers from bloomberg_tickers")
        
        # Show what we have by currency
        cursor.execute("""
            SELECT currency_code, 
                   COUNT(*) as total,
                   COUNT(DISTINCT instrument_type) as types,
                   string_agg(DISTINCT instrument_type, ', ') as type_list
            FROM ticker_reference
            GROUP BY currency_code
            ORDER BY total DESC
        """)
        
        print("\n=== POPULATED DATABASE STATE ===")
        total = 0
        for row in cursor.fetchall():
            print(f"{row[0]}: {row[1]} tickers ({row[3]})")
            total += row[1]
        
        print(f"\nTotal tickers: {total}")
        
        # Show sample tickers for major currencies
        print("\n=== SAMPLE TICKERS ===")
        for currency in ['USD', 'EUR', 'GBP', 'JPY', 'CHF']:
            cursor.execute("""
                SELECT bloomberg_ticker 
                FROM ticker_reference 
                WHERE currency_code = %s 
                ORDER BY bloomberg_ticker 
                LIMIT 5
            """, (currency,))
            
            tickers = [row[0] for row in cursor.fetchall()]
            if tickers:
                print(f"{currency}: {', '.join(tickers)}")
        
        conn.commit()
        print("\n✅ Database population complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()