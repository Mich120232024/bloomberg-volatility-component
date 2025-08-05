#!/usr/bin/env python3
"""
Discover OIS tickers for each currency and populate rate_curve_mappings table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from yield_curve_db_endpoint import get_database_connection
import requests
import json
import time

BLOOMBERG_API_URL = "http://20.172.249.92:8080"
BLOOMBERG_HEADERS = {
    "Authorization": "Bearer test",
    "Content-Type": "application/json"
}

def discover_ois_tickers(currency, max_results=50):
    """Discover OIS tickers for a currency using Bloomberg API"""
    try:
        response = requests.post(
            f"{BLOOMBERG_API_URL}/api/bloomberg/ticker-discovery",
            headers=BLOOMBERG_HEADERS,
            json={
                "search_type": "ois",
                "currency": currency,
                "max_results": max_results
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("tickers", [])
        else:
            print(f"API error for {currency}: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        print(f"Error discovering {currency} OIS tickers: {e}")
        return []

def validate_tickers(tickers):
    """Validate tickers using Bloomberg API"""
    if not tickers:
        return []
        
    try:
        response = requests.post(
            f"{BLOOMBERG_API_URL}/api/bloomberg/validate-tickers",
            headers=BLOOMBERG_HEADERS,
            json=tickers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return [ticker for ticker in data if ticker.get("valid", False)]
        else:
            print(f"Validation API error: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        print(f"Error validating tickers: {e}")
        return []

def parse_tenor_to_days(tenor_str):
    """Parse tenor string to days"""
    if not tenor_str or tenor_str == "UNKNOWN":
        return None
        
    tenor_str = tenor_str.upper().strip()
    
    if tenor_str in ["O/N", "ON", "OVERNIGHT"]:
        return 1
    elif tenor_str.endswith("D"):
        return int(tenor_str[:-1])
    elif tenor_str.endswith("W"):
        return int(tenor_str[:-1]) * 7
    elif tenor_str.endswith("M"):
        return int(tenor_str[:-1]) * 30
    elif tenor_str.endswith("Y"):
        return int(tenor_str[:-1]) * 365
    else:
        # Try to parse as number (assume days)
        try:
            return int(tenor_str)
        except:
            return None

def get_existing_curve_mappings(cursor, curve_name):
    """Get existing mappings for a curve"""
    cursor.execute("""
        SELECT bloomberg_ticker, tenor, sorting_order 
        FROM rate_curve_mappings 
        WHERE curve_name = %s
    """, (curve_name,))
    
    return {row[0]: (row[1], row[2]) for row in cursor.fetchall()}

def populate_curve_mappings_for_currency(currency):
    """Discover and populate curve mappings for a specific currency"""
    print(f"\n=== Processing {currency} ===")
    
    # Connect to database
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        # Get curve definitions for this currency
        cursor.execute("""
            SELECT curve_name, curve_type 
            FROM rate_curve_definitions 
            WHERE currency_code = %s AND is_active = true
        """, (currency,))
        
        curve_defs = cursor.fetchall()
        print(f"Found {len(curve_defs)} curve definitions for {currency}")
        
        for curve_name, curve_type in curve_defs:
            if curve_type != "OIS":
                continue
                
            print(f"\nProcessing {curve_name}...")
            
            # Get existing mappings
            existing_mappings = get_existing_curve_mappings(cursor, curve_name)
            print(f"Found {len(existing_mappings)} existing mappings")
            
            # Discover OIS tickers
            print(f"Discovering OIS tickers for {currency}...")
            discovered_tickers = discover_ois_tickers(currency)
            print(f"Discovered {len(discovered_tickers)} potential tickers")
            
            if not discovered_tickers:
                print(f"No tickers discovered for {currency}")
                continue
            
            # Extract just the ticker symbols
            ticker_symbols = [t.get("ticker", "") for t in discovered_tickers if t.get("ticker")]
            
            # Validate tickers
            print(f"Validating {len(ticker_symbols)} tickers...")
            validated_tickers = validate_tickers(ticker_symbols)
            print(f"Validated {len(validated_tickers)} tickers")
            
            # Check which tickers already exist in bloomberg_tickers table
            ticker_placeholders = ",".join(["%s"] * len(ticker_symbols))
            cursor.execute(f"""
                SELECT bloomberg_ticker, tenor, tenor_numeric 
                FROM bloomberg_tickers 
                WHERE bloomberg_ticker IN ({ticker_placeholders})
                AND currency_code = %s
                AND is_active = true
            """, ticker_symbols + [currency])
            
            existing_tickers = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}
            print(f"Found {len(existing_tickers)} tickers in bloomberg_tickers table")
            
            # Process each validated ticker
            new_mappings = 0
            for ticker_info in validated_tickers:
                ticker = ticker_info.get("ticker", "")
                if not ticker or ticker in existing_mappings:
                    continue
                    
                # Check if ticker exists in bloomberg_tickers table
                if ticker not in existing_tickers:
                    print(f"Warning: {ticker} not found in bloomberg_tickers table")
                    continue
                
                # Get tenor info
                db_tenor, db_tenor_numeric = existing_tickers[ticker]
                
                # Determine sorting order based on tenor
                sorting_order = 999  # Default
                if db_tenor_numeric:
                    sorting_order = int(db_tenor_numeric)
                elif db_tenor:
                    days = parse_tenor_to_days(db_tenor)
                    if days:
                        sorting_order = days
                
                # Insert mapping
                try:
                    cursor.execute("""
                        INSERT INTO rate_curve_mappings 
                        (curve_name, bloomberg_ticker, tenor, currency_code, rate_type, sorting_order)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (curve_name, ticker, db_tenor or "UNKNOWN", currency, "OIS", sorting_order))
                    
                    new_mappings += 1
                    print(f"Added mapping: {curve_name} -> {ticker} ({db_tenor})")
                    
                except Exception as e:
                    print(f"Error inserting mapping for {ticker}: {e}")
            
            print(f"Added {new_mappings} new mappings for {curve_name}")
            
        # Commit changes
        conn.commit()
        print(f"Committed changes for {currency}")
        
    except Exception as e:
        print(f"Error processing {currency}: {e}")
        conn.rollback()
    finally:
        conn.close()

def main():
    """Main function to populate curve mappings for all major currencies"""
    currencies = ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NOK", "SEK"]
    
    for currency in currencies:
        try:
            populate_curve_mappings_for_currency(currency)
            time.sleep(2)  # Rate limiting
        except Exception as e:
            print(f"Failed to process {currency}: {e}")
    
    print("\n=== SUMMARY ===")
    # Show final counts
    conn = get_database_connection()
    cursor = conn.cursor()
    
    for currency in currencies:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM rate_curve_mappings rcm
            JOIN rate_curve_definitions rcd ON rcm.curve_name = rcd.curve_name
            WHERE rcd.currency_code = %s
        """, (currency,))
        
        count = cursor.fetchone()[0]
        print(f"{currency}: {count} curve mappings")
    
    conn.close()

if __name__ == "__main__":
    main()