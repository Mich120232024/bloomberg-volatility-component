#!/usr/bin/env python3
"""
Load all curve points for all currencies in a dataframe
Ensures no duplicates with all tickers for all tenors
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from yield_curve_db_endpoint import get_database_connection
import pandas as pd
import requests
import time
from datetime import datetime

BLOOMBERG_API_URL = "http://20.172.249.92:8080"
HEADERS = {
    "Authorization": "Bearer test",
    "Content-Type": "application/json"
}

def extract_tenor_from_ticker(ticker):
    """Extract tenor from Bloomberg ticker pattern"""
    # Handle monthly patterns (USSOA, USSOB, etc.)
    if len(ticker) > 8 and ticker[-8].isalpha() and ticker[-7:] == ' Curncy':
        month_map = {
            'A': '1M', 'B': '2M', 'C': '3M', 'D': '4M', 'E': '5M', 'F': '6M',
            'G': '7M', 'H': '8M', 'I': '9M', 'J': '10M', 'K': '11M', 'L': '12M'
        }
        month_char = ticker[-8]
        if month_char in month_map:
            return month_map[month_char]
    
    # Handle yearly patterns (USSO1, USSO10, etc.)
    if 'SO' in ticker and ticker.split('SO')[-1].split()[0].replace('M','').isdigit():
        tenor_part = ticker.split('SO')[-1].split()[0]
        if 'M' in tenor_part:
            return tenor_part
        else:
            return f"{tenor_part}Y"
    
    # Handle EESWE patterns for EUR
    if 'EESWE' in ticker:
        parts = ticker.split('EESWE')[-1].split()[0]
        if parts.endswith('M'):
            return parts
        elif parts.isdigit():
            return f"{parts}Y"
    
    # Handle overnight rates
    if 'Index' in ticker:
        return 'ON'
    
    return None

def fetch_market_data(tickers):
    """Fetch current market data for tickers"""
    market_data = {}
    
    # Process in batches
    batch_size = 20
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i+batch_size]
        
        try:
            # Use bloomberg/reference endpoint
            response = requests.post(
                f"{BLOOMBERG_API_URL}/api/bloomberg/reference",
                headers=HEADERS,
                json={
                    "securities": batch,
                    "fields": ["PX_LAST", "CHG_PCT_1D"]
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and 'data' in result:
                    securities_data = result['data'].get('securities_data', [])
                    for sec in securities_data:
                        if sec.get('success'):
                            ticker = sec.get('security')
                            fields = sec.get('fields', {})
                            if 'PX_LAST' in fields:
                                market_data[ticker] = {
                                    'rate': fields.get('PX_LAST'),
                                    'change': fields.get('CHG_PCT_1D', 0)
                                }
            
            time.sleep(0.5)  # Rate limiting
            
        except Exception as e:
            print(f"Error fetching batch {i//batch_size + 1}: {e}")
    
    return market_data

def main():
    """Load all curve points for all currencies"""
    conn = get_database_connection()
    
    try:
        # Load all tickers from ticker_reference
        query = """
            SELECT 
                currency_code,
                bloomberg_ticker,
                instrument_type,
                curve_name
            FROM ticker_reference
            WHERE is_active = true
            ORDER BY currency_code, bloomberg_ticker
        """
        
        df = pd.read_sql(query, conn)
        print(f"Loaded {len(df)} tickers from database")
        
        # Extract tenors
        df['tenor'] = df['bloomberg_ticker'].apply(extract_tenor_from_ticker)
        
        # Remove duplicates (keep first occurrence)
        df_unique = df.drop_duplicates(subset=['currency_code', 'tenor'], keep='first')
        print(f"Unique curve points: {len(df_unique)} (removed {len(df) - len(df_unique)} duplicates)")
        
        # Get list of all unique tickers
        unique_tickers = df_unique['bloomberg_ticker'].tolist()
        
        # Fetch market data
        print("\nFetching market data from Bloomberg...")
        market_data = fetch_market_data(unique_tickers)
        
        # Add market data to dataframe
        df_unique['rate'] = df_unique['bloomberg_ticker'].map(lambda x: market_data.get(x, {}).get('rate'))
        df_unique['change_pct'] = df_unique['bloomberg_ticker'].map(lambda x: market_data.get(x, {}).get('change', 0))
        df_unique['data_available'] = df_unique['rate'].notna()
        
        # Create pivot table for rates
        pivot_rates = df_unique.pivot_table(
            index='currency_code',
            columns='tenor',
            values='rate',
            aggfunc='first'
        )
        
        # Sort columns by tenor order
        tenor_order = ['ON', '1M', '2M', '3M', '4M', '5M', '6M', '7M', '8M', '9M', '10M', '11M', '12M',
                      '15M', '18M', '21M', '2Y', '3Y', '4Y', '5Y', '7Y', '10Y', '15Y', '20Y', '25Y', '30Y']
        
        available_tenors = [t for t in tenor_order if t in pivot_rates.columns]
        pivot_rates = pivot_rates[available_tenors]
        
        # Display results
        print("\n" + "="*80)
        print("ALL YIELD CURVE POINTS BY CURRENCY")
        print("="*80)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total unique curve points: {len(df_unique)}")
        print(f"Currencies: {len(pivot_rates)}")
        print(f"Tenors: {len(available_tenors)}")
        
        # Show summary by currency
        print("\n📊 CURVE POINTS BY CURRENCY:")
        for currency in sorted(df_unique['currency_code'].unique()):
            currency_data = df_unique[df_unique['currency_code'] == currency]
            available = currency_data['data_available'].sum()
            total = len(currency_data)
            tenors = sorted(currency_data['tenor'].dropna().unique(), 
                          key=lambda x: (0 if x == 'ON' else 1, x))
            
            print(f"\n{currency}:")
            print(f"  Total points: {total}")
            print(f"  Data available: {available}/{total} ({available/total*100:.0f}%)")
            print(f"  Tenors: {', '.join(tenors)}")
        
        # Show rate matrix
        print("\n📈 YIELD CURVE RATES (%):")
        print(pivot_rates.round(3))
        
        # Save to CSV
        output_file = 'all_yield_curves.csv'
        df_unique.to_csv(output_file, index=False)
        print(f"\n✅ Full data saved to {output_file}")
        
        # Save pivot table
        pivot_file = 'yield_curve_matrix.csv'
        pivot_rates.to_csv(pivot_file)
        print(f"✅ Rate matrix saved to {pivot_file}")
        
        # Statistics
        print("\n📊 STATISTICS:")
        print(f"  Total tickers: {len(df)}")
        print(f"  Unique curve points: {len(df_unique)}")
        print(f"  Duplicates removed: {len(df) - len(df_unique)}")
        print(f"  Data coverage: {df_unique['data_available'].sum()}/{len(df_unique)} ({df_unique['data_available'].mean()*100:.1f}%)")
        
        # G10 coverage check
        g10 = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD', 'SEK', 'NOK']
        g10_in_data = [c for c in g10 if c in pivot_rates.index]
        print(f"\n🌍 G10 COVERAGE: {len(g10_in_data)}/10")
        print(f"  Present: {', '.join(g10_in_data)}")
        missing_g10 = [c for c in g10 if c not in pivot_rates.index]
        if missing_g10:
            print(f"  Missing: {', '.join(missing_g10)}")
        
        return df_unique
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
    finally:
        conn.close()

if __name__ == "__main__":
    df = main()