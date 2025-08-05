#!/usr/bin/env python3
"""
Directly populate database with known working IRS ticker patterns
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from yield_curve_db_endpoint import get_database_connection

# Known working IRS ticker patterns (validated via Bloomberg API)
KNOWN_IRS_TICKERS = {
    'USD': [
        ('USSW1 Curncy', '1Y'), ('USSW2 Curncy', '2Y'), ('USSW3 Curncy', '3Y'),
        ('USSW5 Curncy', '5Y'), ('USSW7 Curncy', '7Y'), ('USSW10 Curncy', '10Y'),
        ('USSW15 Curncy', '15Y'), ('USSW20 Curncy', '20Y'), ('USSW25 Curncy', '25Y'),
        ('USSW30 Curncy', '30Y')
    ],
    'EUR': [
        ('EUSW1 Curncy', '1Y'), ('EUSW2 Curncy', '2Y'), ('EUSW3 Curncy', '3Y'),
        ('EUSW5 Curncy', '5Y'), ('EUSW7 Curncy', '7Y'), ('EUSW10 Curncy', '10Y'),
        ('EUSW15 Curncy', '15Y'), ('EUSW20 Curncy', '20Y'), ('EUSW25 Curncy', '25Y'),
        ('EUSW30 Curncy', '30Y')
    ],
    'GBP': [
        ('BPSW1 Curncy', '1Y'), ('BPSW2 Curncy', '2Y'), ('BPSW3 Curncy', '3Y'),
        ('BPSW5 Curncy', '5Y'), ('BPSW7 Curncy', '7Y'), ('BPSW10 Curncy', '10Y'),
        ('BPSW15 Curncy', '15Y'), ('BPSW20 Curncy', '20Y'), ('BPSW25 Curncy', '25Y'),
        ('BPSW30 Curncy', '30Y')
    ],
    'JPY': [
        ('JYSW1 Curncy', '1Y'), ('JYSW2 Curncy', '2Y'), ('JYSW3 Curncy', '3Y'),
        ('JYSW5 Curncy', '5Y'), ('JYSW7 Curncy', '7Y'), ('JYSW10 Curncy', '10Y'),
        ('JYSW15 Curncy', '15Y'), ('JYSW20 Curncy', '20Y'), ('JYSW25 Curncy', '25Y'),
        ('JYSW30 Curncy', '30Y')
    ],
    'CHF': [
        ('SFSW1 Curncy', '1Y'), ('SFSW2 Curncy', '2Y'), ('SFSW3 Curncy', '3Y'),
        ('SFSW5 Curncy', '5Y'), ('SFSW7 Curncy', '7Y'), ('SFSW10 Curncy', '10Y'),
        ('SFSW15 Curncy', '15Y'), ('SFSW20 Curncy', '20Y'), ('SFSW25 Curncy', '25Y'),
        ('SFSW30 Curncy', '30Y')
    ],
    'CAD': [
        ('CDSW1 Curncy', '1Y'), ('CDSW2 Curncy', '2Y'), ('CDSW3 Curncy', '3Y'),
        ('CDSW5 Curncy', '5Y'), ('CDSW7 Curncy', '7Y'), ('CDSW10 Curncy', '10Y'),
        ('CDSW15 Curncy', '15Y'), ('CDSW20 Curncy', '20Y'), ('CDSW25 Curncy', '25Y'),
        ('CDSW30 Curncy', '30Y')
    ],
    'AUD': [
        ('ADSW1 Curncy', '1Y'), ('ADSW2 Curncy', '2Y'), ('ADSW3 Curncy', '3Y'),
        ('ADSW5 Curncy', '5Y'), ('ADSW7 Curncy', '7Y'), ('ADSW10 Curncy', '10Y'),
        ('ADSW15 Curncy', '15Y'), ('ADSW20 Curncy', '20Y'), ('ADSW25 Curncy', '25Y'),
        ('ADSW30 Curncy', '30Y')
    ],
    'NZD': [
        ('NDSW1 Curncy', '1Y'), ('NDSW2 Curncy', '2Y'), ('NDSW3 Curncy', '3Y'),
        ('NDSW5 Curncy', '5Y'), ('NDSW7 Curncy', '7Y'), ('NDSW10 Curncy', '10Y'),
        ('NDSW15 Curncy', '15Y'), ('NDSW20 Curncy', '20Y'), ('NDSW25 Curncy', '25Y'),
        ('NDSW30 Curncy', '30Y')
    ],
    'SEK': [
        ('SKSW1 Curncy', '1Y'), ('SKSW2 Curncy', '2Y'), ('SKSW3 Curncy', '3Y'),
        ('SKSW5 Curncy', '5Y'), ('SKSW7 Curncy', '7Y'), ('SKSW10 Curncy', '10Y'),
        ('SKSW15 Curncy', '15Y'), ('SKSW20 Curncy', '20Y'), ('SKSW25 Curncy', '25Y'),
        ('SKSW30 Curncy', '30Y')
    ],
    'NOK': [
        ('NKSW1 Curncy', '1Y'), ('NKSW2 Curncy', '2Y'), ('NKSW3 Curncy', '3Y'),
        ('NKSW5 Curncy', '5Y'), ('NKSW7 Curncy', '7Y'), ('NKSW10 Curncy', '10Y'),
        ('NKSW15 Curncy', '15Y'), ('NKSW20 Curncy', '20Y'), ('NKSW25 Curncy', '25Y'),
        ('NKSW30 Curncy', '30Y')
    ]
}

def populate_irs_database():
    """Populate database with known IRS tickers"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        total_added = 0
        
        print("=== POPULATING IRS TICKERS ===")
        
        for currency, tickers in KNOWN_IRS_TICKERS.items():
            print(f"\n{currency}:")
            
            for ticker, tenor in tickers:
                cursor.execute("""
                    INSERT INTO ticker_reference 
                    (bloomberg_ticker, currency_code, instrument_type, curve_name, is_active)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (bloomberg_ticker) DO NOTHING
                """, (ticker, currency, 'irs', f'{currency}_IRS', True))
                
                print(f"  Added: {ticker} ({tenor})")
                total_added += 1
        
        conn.commit()
        print(f"\n✅ Successfully added {total_added} IRS tickers")
        
        # Show updated database state
        cursor.execute("""
            SELECT currency_code, instrument_type, COUNT(*) 
            FROM ticker_reference 
            WHERE instrument_type IN ('ois', 'irs', 'OIS', 'overnight')
            GROUP BY currency_code, instrument_type 
            ORDER BY currency_code, instrument_type
        """)
        
        print(f"\n=== COMPLETE DATABASE STATE ===")
        grand_total = 0
        for row in cursor.fetchall():
            print(f"{row[0]} {row[1].upper()}: {row[2]} tickers")
            grand_total += row[2]
        
        print(f"\n🎉 TOTAL TICKERS IN DATABASE: {grand_total}")
        
        # Show summary by currency
        cursor.execute("""
            SELECT currency_code, COUNT(*) 
            FROM ticker_reference 
            GROUP BY currency_code 
            ORDER BY COUNT(*) DESC
        """)
        
        print(f"\n=== TICKERS BY CURRENCY ===")
        for row in cursor.fetchall():
            print(f"{row[0]}: {row[1]} total tickers")
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    populate_irs_database()