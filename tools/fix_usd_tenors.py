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

# Fix USD yearly tickers that have wrong tenor_numeric values
usd_fixes = [
    {'ticker': 'USSO1 Curncy', 'correct_days': 365},
    {'ticker': 'USSO2 Curncy', 'correct_days': 730},
    {'ticker': 'USSO3 Curncy', 'correct_days': 1095},
    {'ticker': 'USSO4 Curncy', 'correct_days': 1460},
    {'ticker': 'USSO5 Curncy', 'correct_days': 1825},
    {'ticker': 'USSO6 Curncy', 'correct_days': 2190},
    {'ticker': 'USSO7 Curncy', 'correct_days': 2555},
    {'ticker': 'USSO8 Curncy', 'correct_days': 2920},
    {'ticker': 'USSO9 Curncy', 'correct_days': 3285},
    {'ticker': 'USSO10 Curncy', 'correct_days': 3650},
    {'ticker': 'USSO15 Curncy', 'correct_days': 5475},
    {'ticker': 'USSO20 Curncy', 'correct_days': 7300},
    {'ticker': 'USSO30 Curncy', 'correct_days': 10950},
]

conn = psycopg2.connect(**conn_params)
cursor = conn.cursor()

try:
    print("Fixing USD tenor_numeric values...")
    print("=" * 50)
    
    updated_count = 0
    
    for fix in usd_fixes:
        cursor.execute("""
            SELECT tenor_numeric FROM bloomberg_tickers 
            WHERE bloomberg_ticker = %s
        """, (fix['ticker'],))
        
        result = cursor.fetchone()
        if result:
            current_value = float(result[0])
            if current_value != fix['correct_days']:
                cursor.execute("""
                    UPDATE bloomberg_tickers 
                    SET tenor_numeric = %s 
                    WHERE bloomberg_ticker = %s
                """, (fix['correct_days'], fix['ticker']))
                
                print(f"✓ Updated {fix['ticker']}: {current_value} -> {fix['correct_days']} days")
                updated_count += 1
            else:
                print(f"✓ {fix['ticker']} already correct: {current_value} days")
        else:
            print(f"✗ {fix['ticker']} not found")
    
    conn.commit()
    print(f"\n✓ Updated {updated_count} USD tickers")
    
    # Show updated USD curve
    cursor.execute("""
        SELECT bloomberg_ticker, tenor, tenor_numeric, category
        FROM bloomberg_tickers
        WHERE curve_name = 'USD_OIS'
        ORDER BY tenor_numeric
    """)
    
    print("\nUpdated USD OIS curve:")
    for row in cursor.fetchall():
        ticker, tenor, tenor_numeric, category = row
        days = float(tenor_numeric)
        years = days / 365.0
        print(f"  {ticker:20} {tenor:>5} -> {days:>6.0f} days ({years:.3f}Y)")
        
except Exception as e:
    conn.rollback()
    print(f"✗ Error: {e}")
finally:
    cursor.close()
    conn.close()