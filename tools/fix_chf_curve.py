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

# CHF SFSNT tickers that should be part of CHF_OIS curve
chf_fixes = [
    {'ticker': 'SFSNT1 BGNL Curncy', 'tenor': '1M', 'tenor_numeric': 30, 'description': 'CHF OIS 1M'},
    {'ticker': 'SFSNT2 BGNL Curncy', 'tenor': '2M', 'tenor_numeric': 60, 'description': 'CHF OIS 2M'},
    {'ticker': 'SFSNT3 BGNL Curncy', 'tenor': '3M', 'tenor_numeric': 90, 'description': 'CHF OIS 3M'},
    {'ticker': 'SFSNT1Z BGNL Curncy', 'tenor': '1Y', 'tenor_numeric': 365, 'description': 'CHF OIS 1Y'},
    {'ticker': 'SFSNT2Z BGNL Curncy', 'tenor': '2Y', 'tenor_numeric': 730, 'description': 'CHF OIS 2Y'},
    {'ticker': 'SFSNT5 BGNL Curncy', 'tenor': '5Y', 'tenor_numeric': 1825, 'description': 'CHF OIS 5Y'},
    {'ticker': 'SFSNT10 BGNL Curncy', 'tenor': '10Y', 'tenor_numeric': 3650, 'description': 'CHF OIS 10Y'},
]

conn = psycopg2.connect(**conn_params)
cursor = conn.cursor()

try:
    print("Fixing CHF curve assignments...")
    print("=" * 50)
    
    updated_count = 0
    
    for fix in chf_fixes:
        # Update the ticker to be part of CHF_OIS curve
        cursor.execute("""
            UPDATE bloomberg_tickers 
            SET curve_name = 'CHF_OIS',
                category = 'OIS',
                tenor = %s,
                tenor_numeric = %s,
                description = %s
            WHERE bloomberg_ticker = %s
        """, (fix['tenor'], fix['tenor_numeric'], fix['description'], fix['ticker']))
        
        if cursor.rowcount > 0:
            print(f"✓ Updated {fix['ticker']} -> CHF_OIS {fix['tenor']}")
            updated_count += 1
        else:
            print(f"✗ {fix['ticker']} not found")
    
    conn.commit()
    print(f"\n✓ Updated {updated_count} CHF tickers")
    
    # Show updated CHF curve
    cursor.execute("""
        SELECT bloomberg_ticker, tenor, tenor_numeric, category
        FROM bloomberg_tickers
        WHERE curve_name = 'CHF_OIS'
        ORDER BY tenor_numeric
    """)
    
    print("\nUpdated CHF OIS curve:")
    for row in cursor.fetchall():
        ticker, tenor, tenor_numeric, category = row
        days = float(tenor_numeric)
        years = days / 365.0
        print(f"  {ticker:25} {tenor:>5} -> {days:>6.0f} days ({years:.3f}Y)")
        
except Exception as e:
    conn.rollback()
    print(f"✗ Error: {e}")
finally:
    cursor.close()
    conn.close()