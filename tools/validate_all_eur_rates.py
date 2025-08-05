#!/usr/bin/env python3
import requests
import psycopg2

# Get all EUR tickers from database
conn_params = {
    'host': 'gzcdevserver.postgres.database.azure.com',
    'database': 'gzc_platform',
    'user': 'mikael',
    'port': 5432,
    'password': 'Ii89rra137+*',
    'sslmode': 'require'
}

conn = psycopg2.connect(**conn_params)
cursor = conn.cursor()

cursor.execute("""
    SELECT bloomberg_ticker, tenor
    FROM bloomberg_tickers
    WHERE currency_code = 'EUR'
    ORDER BY bloomberg_ticker
""")

tickers = cursor.fetchall()
cursor.close()
conn.close()

print("Validating all EUR tickers with Bloomberg API...")
print("=" * 60)

# Check each ticker
bloomberg_url = "http://20.172.249.92:8080"
invalid_tickers = []

for ticker, tenor in tickers:
    response = requests.post(
        f"{bloomberg_url}/api/bloomberg/reference",
        headers={"Authorization": "Bearer test"},
        json={
            "securities": [ticker],
            "fields": ["PX_LAST", "NAME"]
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        if "data" in data and "securities_data" in data["data"]:
            for sec_data in data["data"]["securities_data"]:
                if sec_data.get("success"):
                    rate = sec_data["fields"].get("PX_LAST")
                    name = sec_data["fields"].get("NAME", "")
                    
                    # Check if rate is reasonable for EUR (between -1% and 5%)
                    if rate is None:
                        print(f"✗ {ticker} ({tenor}): No rate data")
                        invalid_tickers.append(ticker)
                    elif rate < -1 or rate > 5:
                        print(f"✗ {ticker} ({tenor}): {rate:.4f}% - INVALID RATE")
                        invalid_tickers.append(ticker)
                    else:
                        print(f"✓ {ticker} ({tenor}): {rate:.4f}% - {name}")

print(f"\n{len(invalid_tickers)} tickers with invalid data:")
for t in invalid_tickers:
    print(f"  - {t}")