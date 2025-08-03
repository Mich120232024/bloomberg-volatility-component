#!/usr/bin/env python3
"""
Populate ticker_reference with all G10 OIS curves
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from yield_curve_db_endpoint import get_database_connection

# OIS ticker patterns for all G10 currencies
OIS_PATTERNS = {
    'EUR': ('EESWE', 'EUR_ESTR_OIS'),      # ESTR OIS
    'GBP': ('SONIO', 'GBP_SONIA_OIS'),     # SONIA OIS  
    'CHF': ('SSARON', 'CHF_SARON_OIS'),    # SARON OIS
    'CAD': ('CDSO', 'CAD_CORRA_OIS'),      # CORRA OIS
    'AUD': ('RBAO', 'AUD_AONIA_OIS'),      # AONIA OIS
    'NZD': ('NDSO', 'NZD_NZIONA_OIS'),     # NZIONA OIS
    'SEK': ('SKSO', 'SEK_STIBOR_OIS'),     # STIBOR OIS
    'NOK': ('NKSO', 'NOK_NOWA_OIS'),       # NOWA OIS
}

# Standard tenors (same as USD)
STANDARD_TENORS = [1, 2, 3, 5, 7, 10, 15, 20, 30]

def populate_ois_curves():
    """Populate all missing G10 OIS curves"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        # Check what's already there
        cursor.execute("SELECT DISTINCT currency_code FROM ticker_reference WHERE is_active = true")
        existing = [row[0] for row in cursor.fetchall()]
        print(f"Existing currencies: {existing}")
        
        added_count = 0
        
        for currency, (prefix, curve_name) in OIS_PATTERNS.items():
            if currency in existing:
                print(f"\n{currency} already exists, skipping")
                continue
                
            print(f"\nAdding {currency} OIS curve ({curve_name}):")
            
            for tenor in STANDARD_TENORS:
                ticker = f"{prefix}{tenor} Curncy"
                
                cursor.execute("""
                    INSERT INTO ticker_reference 
                    (bloomberg_ticker, currency_code, instrument_type, curve_name, is_active)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (bloomberg_ticker) DO NOTHING
                """, (ticker, currency, 'ois', curve_name, True))
                
                if cursor.rowcount > 0:
                    print(f"  Added: {ticker}")
                    added_count += 1
        
        conn.commit()
        print(f"\n✅ Added {added_count} new tickers")
        
        # Show final state
        cursor.execute("""
            SELECT currency_code, COUNT(*) 
            FROM ticker_reference 
            WHERE is_active = true
            GROUP BY currency_code
            ORDER BY currency_code
        """)
        
        print("\n=== FINAL CURVE STATUS ===")
        for row in cursor.fetchall():
            print(f"{row[0]}: {row[1]} tickers")
            
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    populate_ois_curves()