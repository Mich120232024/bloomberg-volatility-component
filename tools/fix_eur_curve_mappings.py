#!/usr/bin/env python3
"""
Fix EUR curve mappings to use correct ticker symbols that exist in bloomberg_tickers table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from yield_curve_db_endpoint import get_database_connection

def fix_eur_curve_mappings():
    """Replace wrong EUR mappings with correct ones from bloomberg_tickers"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        print("=== Fixing EUR Curve Mappings ===")
        
        # First, clear the incorrect EUR mappings
        cursor.execute("DELETE FROM rate_curve_mappings WHERE currency_code = 'EUR'")
        deleted_count = cursor.rowcount
        print(f"Deleted {deleted_count} incorrect EUR mappings")
        
        # Get all EUR tickers from bloomberg_tickers that could be part of OIS curves
        cursor.execute("""
            SELECT bloomberg_ticker, tenor, tenor_numeric, category
            FROM bloomberg_tickers 
            WHERE currency_code = 'EUR' 
            AND is_active = true
            AND tenor_numeric IS NOT NULL
            ORDER BY tenor_numeric
        """)
        
        eur_tickers = cursor.fetchall()
        print(f"Found {len(eur_tickers)} EUR tickers in bloomberg_tickers")
        
        # Create mappings for EUR_ESTR_OIS curve
        curve_name = "EUR_ESTR_OIS"
        added_count = 0
        
        for ticker, tenor, tenor_numeric, category in eur_tickers:
            # Determine rate type based on ticker
            rate_type = "OIS"
            if "ESTR" in ticker.upper() or "EUR" in ticker.upper():
                rate_type = "OIS"
            
            # Use tenor_numeric as sorting order
            sorting_order = int(tenor_numeric) if tenor_numeric else 999
            
            # Insert new mapping
            cursor.execute("""
                INSERT INTO rate_curve_mappings 
                (curve_name, bloomberg_ticker, tenor, currency_code, rate_type, sorting_order)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (curve_name, ticker, tenor, "EUR", rate_type, sorting_order))
            
            added_count += 1
            print(f"Added: {curve_name} -> {ticker} ({tenor}, {sorting_order} days)")
        
        # Commit changes
        conn.commit()
        print(f"\nSuccessfully added {added_count} new EUR curve mappings")
        
        # Verify the fix
        cursor.execute("""
            SELECT COUNT(*) 
            FROM rate_curve_definitions rcd
            JOIN rate_curve_mappings rcm ON rcd.curve_name = rcm.curve_name
            JOIN bloomberg_tickers bt ON bt.bloomberg_ticker = rcm.bloomberg_ticker
            WHERE rcd.currency_code = 'EUR'
            AND rcd.is_active = true
            AND bt.is_active = true
        """)
        
        working_count = cursor.fetchone()[0]
        print(f"Verification: {working_count} EUR mappings now properly joined")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_eur_curve_mappings()