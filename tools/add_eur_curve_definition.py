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
    # First check what columns exist
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'rate_curve_definitions'
        ORDER BY ordinal_position
    """)
    
    columns = [row[0] for row in cursor.fetchall()]
    print("Columns in rate_curve_definitions:", columns)
    
    # Add EUR_OIS curve definition with only required columns
    cursor.execute("""
        INSERT INTO rate_curve_definitions (
            curve_name,
            currency_code,
            curve_type,
            primary_use,
            methodology
        ) VALUES (
            'EUR_OIS',
            'EUR',
            'OIS',
            'FX Options Pricing',
            'European €STR-based overnight index swap curve'
        )
    """)
    
    conn.commit()
    print("✓ Added EUR_OIS to rate_curve_definitions")
    
    # Verify
    cursor.execute("""
        SELECT curve_name, currency_code, curve_type, methodology
        FROM rate_curve_definitions
        WHERE curve_type = 'OIS'
        ORDER BY currency_code
    """)
    
    print("\nOIS curves in database:")
    for row in cursor.fetchall():
        print(f"  {row[0]:15} {row[1]:5} {row[2]:10} {row[3]}")
        
except Exception as e:
    conn.rollback()
    print(f"✗ Error: {e}")
finally:
    cursor.close()
    conn.close()