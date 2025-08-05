#!/usr/bin/env python3
import psycopg2
import json

# Connect to PostgreSQL
conn = psycopg2.connect(
    dbname="gzc_platform",
    user="mikaeleage",
    password="12421",
    host="localhost",
    port="5432"
)

cursor = conn.cursor()

# List all tables
cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    ORDER BY table_name;
""")
tables = cursor.fetchall()
print("TABLES IN DATABASE:")
for table in tables:
    print(f"  - {table[0]}")

# Check for rate curve related tables
print("\nRATE CURVE RELATED TABLES:")
cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND (table_name LIKE '%rate%' OR table_name LIKE '%curve%')
    ORDER BY table_name;
""")
rate_tables = cursor.fetchall()
for table in rate_tables:
    print(f"  - {table[0]}")
    
    # Get columns for each rate table
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = %s 
        ORDER BY ordinal_position;
    """, (table[0],))
    columns = cursor.fetchall()
    for col in columns:
        print(f"    * {col[0]} ({col[1]})")

# Check bloomberg_tickers table
print("\nBLOOMBERG_TICKERS TABLE:")
cursor.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'bloomberg_tickers' 
    ORDER BY ordinal_position;
""")
columns = cursor.fetchall()
if columns:
    for col in columns:
        print(f"  - {col[0]} ({col[1]})")
        
    # Count tickers by currency
    cursor.execute("""
        SELECT currency, COUNT(*) as count 
        FROM bloomberg_tickers 
        GROUP BY currency 
        ORDER BY currency;
    """)
    counts = cursor.fetchall()
    print("\nTICKER COUNTS BY CURRENCY:")
    for currency, count in counts:
        print(f"  {currency}: {count} tickers")
        
    # Show USD OIS tickers
    cursor.execute("""
        SELECT ticker, description 
        FROM bloomberg_tickers 
        WHERE currency = 'USD' 
        AND ticker LIKE '%OIS%' OR ticker LIKE '%SOFR%'
        ORDER BY ticker;
    """)
    usd_ois = cursor.fetchall()
    print("\nUSD OIS/SOFR TICKERS:")
    for ticker, desc in usd_ois:
        print(f"  {ticker}: {desc}")

conn.close()