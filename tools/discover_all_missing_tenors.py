#!/usr/bin/env python3
import requests
import psycopg2
import time

# Database connection
conn_params = {
    'host': 'gzcdevserver.postgres.database.azure.com',
    'database': 'gzc_platform',
    'user': 'mikael',
    'port': 5432,
    'password': 'Ii89rra137+*',
    'sslmode': 'require'
}

bloomberg_url = "http://20.172.249.92:8080"

def discover_ois_tickers(currency):
    """Discover OIS tickers for a currency"""
    try:
        response = requests.post(
            f"{bloomberg_url}/api/bloomberg/ticker-discovery",
            headers={"Authorization": "Bearer test"},
            json={
                "search_type": "ois",
                "currency": currency,
                "max_results": 100
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and "tickers" in data:
                return data["tickers"]
        return []
    except Exception as e:
        print(f"Error discovering {currency} OIS: {e}")
        return []

def discover_irs_tickers(currency):
    """Discover IRS tickers for a currency"""
    try:
        response = requests.post(
            f"{bloomberg_url}/api/bloomberg/ticker-discovery",
            headers={"Authorization": "Bearer test"},
            json={
                "search_type": "irs", 
                "currency": currency,
                "max_results": 100
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and "tickers" in data:
                return data["tickers"]
        return []
    except Exception as e:
        print(f"Error discovering {currency} IRS: {e}")
        return []

def validate_tickers(tickers):
    """Validate tickers with Bloomberg"""
    if not tickers:
        return []
    
    try:
        response = requests.post(
            f"{bloomberg_url}/api/bloomberg/validate-tickers",
            headers={"Authorization": "Bearer test"},
            json=tickers[:50],  # Limit batch size
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and "results" in data:
                return [r for r in data["results"] if r.get("valid")]
        return []
    except Exception as e:
        print(f"Error validating tickers: {e}")
        return []

# Connect to database
conn = psycopg2.connect(**conn_params)
cursor = conn.cursor()

# G10 currencies and their curve types
currency_config = {
    'USD': 'ois',
    'EUR': 'ois', 
    'GBP': 'ois',
    'JPY': 'ois',
    'CHF': 'ois',
    'CAD': 'ois',
    'AUD': 'ois',
    'NZD': 'ois',
    'SEK': 'irs',  # SEK uses IRS
    'NOK': 'irs'   # NOK uses IRS
}

try:
    print("Discovering missing tenors for all G10 currencies...")
    print("=" * 80)
    
    for currency, curve_type in currency_config.items():
        print(f"\n{currency} ({curve_type.upper()}):")
        print("-" * 40)
        
        # Get existing tickers
        cursor.execute("""
            SELECT bloomberg_ticker FROM bloomberg_tickers 
            WHERE currency_code = %s AND curve_name IS NOT NULL
        """, (currency,))
        existing_tickers = {row[0] for row in cursor.fetchall()}
        
        # Discover new tickers
        if curve_type == 'ois':
            discovered = discover_ois_tickers(currency)
        else:
            discovered = discover_irs_tickers(currency)
        
        print(f"Discovered {len(discovered)} {curve_type.upper()} tickers")
        
        # Find new tickers (discovered are dictionaries with 'ticker' key)
        discovered_ticker_names = [t.get('ticker', '') for t in discovered if isinstance(t, dict)]
        new_tickers = [t for t in discovered_ticker_names if t and t not in existing_tickers]
        print(f"New tickers: {len(new_tickers)}")
        
        if new_tickers:
            # Validate new tickers
            print("Validating new tickers...")
            valid_tickers = validate_tickers(new_tickers)
            print(f"Valid new tickers: {len(valid_tickers)}")
            
            # Show first 10 new valid tickers
            for i, ticker_data in enumerate(valid_tickers[:10]):
                ticker = ticker_data['ticker']
                price = ticker_data.get('price', 'N/A')
                print(f"  {i+1:2}. {ticker:<25} -> {price}")
            
            if len(valid_tickers) > 10:
                print(f"  ... and {len(valid_tickers) - 10} more")
        
        time.sleep(2)  # Rate limiting
        
except KeyboardInterrupt:
    print("\nInterrupted by user")
except Exception as e:
    print(f"Error: {e}")
finally:
    cursor.close()
    conn.close()