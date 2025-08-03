#!/usr/bin/env python3
import psycopg2
import requests

# First, remove the incorrect EUR tickers from database
conn_params = {
    'host': 'gzcdevserver.postgres.database.azure.com',
    'database': 'gzc_platform',
    'user': 'mikael',
    'port': 5432,
    'password': 'Ii89rra137+*',
    'sslmode': 'require'
}

print("Fixing EUR OIS tickers...")
print("=" * 60)

# Connect to database
conn = psycopg2.connect(**conn_params)
cursor = conn.cursor()

try:
    # First, remove all incorrect EUR tickers
    print("1. Removing incorrect EUR tickers...")
    cursor.execute("""
        DELETE FROM bloomberg_tickers 
        WHERE (bloomberg_ticker LIKE 'EUR%' OR bloomberg_ticker LIKE 'EESWE%')
        AND bloomberg_ticker != 'ESTR Index'
    """)
    deleted_count = cursor.rowcount
    print(f"   Removed {deleted_count} incorrect tickers")
    
    # Now let's discover proper EUR OIS tickers using the discovery endpoint
    print("\n2. Discovering correct EUR OIS tickers...")
    response = requests.post(
        "http://20.172.249.92:8080/api/bloomberg/ticker-discovery",
        headers={"Authorization": "Bearer test"},
        json={
            "search_type": "ois", 
            "currency": "EUR",
            "max_results": 50
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        if "tickers" in data and data["tickers"]:
            print(f"   Found {len(data['tickers'])} EUR OIS tickers")
            
            # Validate each ticker
            print("\n3. Validating discovered tickers...")
            valid_tickers = []
            
            for ticker_info in data["tickers"]:
                ticker = ticker_info["ticker"]
                validation_response = requests.post(
                    "http://20.172.249.92:8080/api/bloomberg/reference",
                    headers={"Authorization": "Bearer test"},
                    json={
                        "securities": [ticker],
                        "fields": ["PX_LAST", "DESCRIPTION", "NAME"]
                    }
                )
                
                if validation_response.status_code == 200:
                    validation_data = validation_response.json()
                    if ticker in validation_data:
                        px_last = validation_data[ticker].get("PX_LAST")
                        description = validation_data[ticker].get("DESCRIPTION", "")
                        
                        # Check if this looks like a valid rate (between -5 and 10)
                        if px_last is not None and -5 < px_last < 10:
                            valid_tickers.append({
                                "ticker": ticker,
                                "description": description,
                                "rate": px_last
                            })
                            print(f"   ✓ {ticker}: {px_last:.4f}% - {description}")
                        else:
                            print(f"   ✗ {ticker}: Invalid rate {px_last}")
            
            # If we didn't find enough tickers, try known EUR swap tickers
            if len(valid_tickers) < 5:
                print("\n4. Trying known EUR swap curve tickers...")
                known_tickers = [
                    "YCSW0045 Index",  # Bloomberg EUR swaps curve
                    "ESTR Index",      # Euro Short-Term Rate
                    "ESTRON Index",    # ESTR Overnight
                    "EUR006M Index",   # 6M EURIBOR
                    "EUR003M Index"    # 3M EURIBOR
                ]
                
                for ticker in known_tickers:
                    response = requests.post(
                        "http://20.172.249.92:8080/api/bloomberg/reference",
                        headers={"Authorization": "Bearer test"},
                        json={
                            "securities": [ticker],
                            "fields": ["PX_LAST", "DESCRIPTION", "NAME"]
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if ticker in data and data[ticker].get("PX_LAST") is not None:
                            rate = data[ticker]["PX_LAST"]
                            desc = data[ticker].get("DESCRIPTION", "")
                            if -5 < rate < 10:
                                print(f"   ✓ {ticker}: {rate:.4f}% - {desc}")
                                # Check if not already in valid_tickers
                                if not any(t["ticker"] == ticker for t in valid_tickers):
                                    valid_tickers.append({
                                        "ticker": ticker,
                                        "description": desc,
                                        "rate": rate
                                    })
            
            print(f"\n5. Found {len(valid_tickers)} valid EUR OIS/swap tickers")
            
            # Ask user before adding to database
            if valid_tickers:
                print("\nValid tickers found:")
                for t in valid_tickers:
                    print(f"  {t['ticker']:20} {t['rate']:7.4f}% - {t['description']}")
                
                print("\nThese tickers will be added to the database.")
                
        else:
            print("   No EUR OIS tickers found via discovery")
            
            # Try manual pattern search
            print("\n3. Trying manual pattern search...")
            patterns = [
                ("ESTRON", "Index"),
                ("ESTR", "Index"),
                ("YCSW0045", "Index"),
                ("EUSWEA", "Curncy"),  # EUR swap annual
                ("EUSWEC", "Curncy"),  # EUR swap semi-annual
            ]
            
            for prefix, suffix in patterns:
                ticker = f"{prefix} {suffix}"
                response = requests.post(
                    "http://20.172.249.92:8080/api/bloomberg/reference",
                    headers={"Authorization": "Bearer test"},
                    json={
                        "securities": [ticker],
                        "fields": ["PX_LAST", "DESCRIPTION", "NAME"]
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if ticker in data and data[ticker].get("PX_LAST") is not None:
                        print(f"   Found: {ticker} - {data[ticker].get('DESCRIPTION', 'N/A')}")
    
    else:
        print(f"   Discovery failed: {response.status_code}")
        print(response.text)
        
    # For now, let's keep ESTR Index as the overnight rate
    print("\n6. Ensuring ESTR Index remains for overnight rate...")
    cursor.execute("""
        SELECT bloomberg_ticker, currency_code FROM bloomberg_tickers
        WHERE bloomberg_ticker = 'ESTR Index'
    """)
    
    if cursor.fetchone() is None:
        # Re-add ESTR Index if it was deleted
        cursor.execute("""
            INSERT INTO bloomberg_tickers (bloomberg_ticker, currency_code, tenor, tenor_numeric, curve_name, category)
            VALUES ('ESTR Index', 'EUR', 'O/N', 1, 'EUR_OIS', 'RATE')
        """)
        print("   Re-added ESTR Index")
    else:
        print("   ESTR Index already exists")
    
    conn.commit()
    print("\n✓ EUR OIS tickers have been updated")
    
except Exception as e:
    conn.rollback()
    print(f"\n✗ Error: {e}")
    
finally:
    cursor.close()
    conn.close()

print("\nNext steps:")
print("1. Manually verify EUR OIS tickers on Bloomberg Terminal")
print("2. Add validated tickers to database")
print("3. Update gateway tenor conversion logic if needed")