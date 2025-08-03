#!/usr/bin/env python3
import psycopg2

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

try:
    # Check rate_curve_definitions
    print("Checking rate_curve_definitions table:")
    cursor.execute("""
        SELECT curve_name, currency_code, curve_type, primary_use
        FROM rate_curve_definitions
        WHERE curve_type = 'OIS'
        ORDER BY currency_code
    """)
    
    for row in cursor.fetchall():
        print(f"  {row[0]:15} {row[1]:5} {row[2]:10} {row[3]}")
        
    # Check if EUR_OIS exists
    cursor.execute("""
        SELECT COUNT(*) FROM rate_curve_definitions
        WHERE curve_name = 'EUR_OIS'
    """)
    
    count = cursor.fetchone()[0]
    print(f"\nEUR_OIS exists in rate_curve_definitions: {'Yes' if count > 0 else 'No'}")
    
    # If not exists, we need to add it
    if count == 0:
        print("\nNeed to add EUR_OIS to rate_curve_definitions table")
        
finally:
    cursor.close()
    conn.close()