#!/usr/bin/env python3
import psycopg2
import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Azure Key Vault connection
credential = DefaultAzureCredential()
key_vault_url = "https://kv-gzc-platform-prod.vault.azure.net/"
secret_client = SecretClient(vault_url=key_vault_url, credential=credential)

# Get PostgreSQL connection from Key Vault
db_connection_string = secret_client.get_secret("database-connection-string").value

# Parse connection string for psycopg2
# Expected format: "host=psql-gzc-platform-prod.postgres.database.azure.com port=5432 dbname=gzc_platform user=gzcadmin password=..."
conn_params = {}
for param in db_connection_string.split():
    key, value = param.split('=')
    conn_params[key] = value

# Connect to Azure PostgreSQL
conn = psycopg2.connect(**conn_params)
cursor = conn.cursor()

try:
    # Insert USD OIS curve definition
    cursor.execute("""
        INSERT INTO rate_curve_definitions (curve_name, curve_type, currency, active)
        VALUES ('USD_OIS', 'OIS', 'USD', true)
        ON CONFLICT (curve_name) DO UPDATE SET active = true
        RETURNING id
    """)
    curve_id = cursor.fetchone()[0]
    print(f"USD OIS curve ID: {curve_id}")

    # Insert all 21 USD OIS tickers
    tickers = [
        ('USSOA Curncy', 'USD SOFR OIS 1M', '1M', 30),
        ('USSOB Curncy', 'USD SOFR OIS 2M', '2M', 60),
        ('USSOC Curncy', 'USD SOFR OIS 3M', '3M', 90),
        ('USSOD Curncy', 'USD SOFR OIS 4M', '4M', 120),
        ('USSOE Curncy', 'USD SOFR OIS 5M', '5M', 150),
        ('USSOF Curncy', 'USD SOFR OIS 6M', '6M', 180),
        ('USSOG Curncy', 'USD SOFR OIS 7M', '7M', 210),
        ('USSOH Curncy', 'USD SOFR OIS 8M', '8M', 240),
        ('USSOI Curncy', 'USD SOFR OIS 9M', '9M', 270),
        ('USSOJ Curncy', 'USD SOFR OIS 10M', '10M', 300),
        ('USSOK Curncy', 'USD SOFR OIS 11M', '11M', 330),
        ('USSO1 Curncy', 'USD SOFR OIS 1Y', '1Y', 365),
        ('USSO2 Curncy', 'USD SOFR OIS 2Y', '2Y', 730),
        ('USSO3 Curncy', 'USD SOFR OIS 3Y', '3Y', 1095),
        ('USSO4 Curncy', 'USD SOFR OIS 4Y', '4Y', 1460),
        ('USSO5 Curncy', 'USD SOFR OIS 5Y', '5Y', 1825),
        ('USSO6 Curncy', 'USD SOFR OIS 6Y', '6Y', 2190),
        ('USSO7 Curncy', 'USD SOFR OIS 7Y', '7Y', 2555),
        ('USSO8 Curncy', 'USD SOFR OIS 8Y', '8Y', 2920),
        ('USSO9 Curncy', 'USD SOFR OIS 9Y', '9Y', 3285),
        ('USSO10 Curncy', 'USD SOFR OIS 10Y', '10Y', 3650)
    ]

    # Insert tickers
    for ticker, desc, tenor, days in tickers:
        cursor.execute("""
            INSERT INTO bloomberg_tickers (ticker, description, currency, instrument_type, active)
            VALUES (%s, %s, 'USD', 'OIS', true)
            ON CONFLICT (ticker) DO UPDATE SET active = true
            RETURNING id
        """, (ticker, desc))
        ticker_id = cursor.fetchone()[0]
        
        # Insert curve membership
        cursor.execute("""
            INSERT INTO rate_curve_memberships (curve_id, ticker_id, tenor, tenor_days, sequence_order)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (curve_id, ticker_id) DO UPDATE SET tenor_days = EXCLUDED.tenor_days
        """, (curve_id, ticker_id, tenor, days, tickers.index((ticker, desc, tenor, days)) + 1))
    
    conn.commit()
    print("Successfully inserted USD OIS curve with 21 tickers")
    
    # Verify
    cursor.execute("""
        SELECT COUNT(*) FROM rate_curve_memberships 
        WHERE curve_id = %s
    """, (curve_id,))
    count = cursor.fetchone()[0]
    print(f"Total tickers in USD OIS curve: {count}")
    
except Exception as e:
    conn.rollback()
    print(f"Error: {e}")
    raise
finally:
    cursor.close()
    conn.close()