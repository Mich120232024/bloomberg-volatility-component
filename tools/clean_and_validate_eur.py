#!/usr/bin/env python3
import psycopg2
import requests

conn_params = {
    'host': 'gzcdevserver.postgres.database.azure.com',
    'database': 'gzc_platform',
    'user': 'mikael',
    'port': 5432,
    'password': 'Ii89rra137+*',
    'sslmode': 'require'
}

bloomberg_url = "http://20.172.249.92:8080"

print("Cleaning and validating EUR tickers...")
print("=" * 60)

# First, get all current EUR tickers
conn = psycopg2.connect(**conn_params)
cursor = conn.cursor()

try:
    # Get all EUR tickers
    cursor.execute("""
        SELECT bloomberg_ticker, tenor, tenor_numeric 
        FROM bloomberg_tickers 
        WHERE currency_code = 'EUR'
        ORDER BY bloomberg_ticker
    """)
    
    current_tickers = cursor.fetchall()
    print(f"Found {len(current_tickers)} EUR tickers in database")
    
    # Validate each ticker
    print("\nValidating tickers with Bloomberg...")
    valid_tickers = []
    invalid_tickers = []
    
    for ticker, tenor, tenor_numeric in current_tickers:
        response = requests.post(
            f"{bloomberg_url}/api/bloomberg/reference",
            headers={"Authorization": "Bearer test"},
            json={
                "securities": [ticker],
                "fields": ["PX_LAST", "DESCRIPTION", "NAME"]
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "securities_data" in data["data"]:
                for sec_data in data["data"]["securities_data"]:
                    if sec_data["security"] == ticker and sec_data.get("fields", {}).get("PX_LAST") is not None:
                        rate = sec_data["fields"]["PX_LAST"]
                        # Check if rate is reasonable (between -5% and 10%)
                        if -5 < rate < 10:
                            print(f"✓ {ticker}: {rate:.4f}% - Valid")
                            valid_tickers.append(ticker)
                        else:
                            print(f"✗ {ticker}: {rate} - Invalid rate (outside -5% to 10%)")
                            invalid_tickers.append(ticker)
                    else:
                        print(f"✗ {ticker}: No data")
                        invalid_tickers.append(ticker)
    
    # Remove invalid tickers
    if invalid_tickers:
        print(f"\nRemoving {len(invalid_tickers)} invalid tickers...")
        for ticker in invalid_tickers:
            cursor.execute("""
                DELETE FROM bloomberg_tickers 
                WHERE bloomberg_ticker = %s
            """, (ticker,))
            print(f"  Removed: {ticker}")
    
    # Try to find valid EUR rate tickers
    print("\nSearching for valid EUR rate tickers...")
    test_patterns = [
        # EURIBOR rates
        ("EUR001M", "Index", "1M", 30),
        ("EUR002M", "Index", "2M", 60),
        ("EUR003M", "Index", "3M", 90),
        ("EUR006M", "Index", "6M", 180),
        ("EUR012M", "Index", "12M", 365),
        
        # Alternative ESTR pattern
        ("ESTRON", "Index", "O/N", 1),
        
        # EUR deposit rates
        ("EUDR1T", "Curncy", "O/N", 1),
        ("EUDR1W", "Curncy", "1W", 7),
        ("EUDR1M", "Curncy", "1M", 30),
    ]
    
    for prefix, suffix, tenor, tenor_days in test_patterns:
        ticker = f"{prefix} {suffix}"
        if ticker not in valid_tickers:
            response = requests.post(
                f"{bloomberg_url}/api/bloomberg/reference",
                headers={"Authorization": "Bearer test"},
                json={
                    "securities": [ticker],
                    "fields": ["PX_LAST", "DESCRIPTION"]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and "securities_data" in data["data"]:
                    for sec_data in data["data"]["securities_data"]:
                        if sec_data.get("fields", {}).get("PX_LAST") is not None:
                            rate = sec_data["fields"]["PX_LAST"]
                            if -5 < rate < 10:
                                print(f"✓ Found valid ticker: {ticker} = {rate:.4f}%")
                                # Add to database
                                cursor.execute("""
                                    INSERT INTO bloomberg_tickers (
                                        bloomberg_ticker, currency_code, tenor, 
                                        tenor_numeric, curve_name, category
                                    ) VALUES (%s, %s, %s, %s, %s, %s)
                                    ON CONFLICT (bloomberg_ticker) DO NOTHING
                                """, (ticker, 'EUR', tenor, tenor_days, 'EUR_OIS', 'RATE'))
    
    conn.commit()
    
    # Final count
    cursor.execute("""
        SELECT COUNT(*) FROM bloomberg_tickers 
        WHERE currency_code = 'EUR'
    """)
    final_count = cursor.fetchone()[0]
    
    print(f"\n✓ Cleanup complete")
    print(f"  Valid tickers kept: {len(valid_tickers)}")
    print(f"  Invalid tickers removed: {len(invalid_tickers)}")
    print(f"  Final EUR ticker count: {final_count}")
    
except Exception as e:
    conn.rollback()
    print(f"✗ Error: {e}")
finally:
    cursor.close()
    conn.close()