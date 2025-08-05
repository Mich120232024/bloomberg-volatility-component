#!/usr/bin/env python3
import psycopg2
import requests
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

gateway_url = "http://localhost:8000"

def check_database_coverage():
    """Check database ticker coverage for all G10 currencies"""
    conn = psycopg2.connect(**conn_params)
    cursor = conn.cursor()
    
    print("DATABASE COVERAGE ANALYSIS")
    print("=" * 80)
    
    currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD', 'SEK', 'NOK']
    
    for currency in currencies:
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN curve_name IS NOT NULL THEN 1 END) as with_curve,
                   COUNT(CASE WHEN curve_name IS NULL THEN 1 END) as without_curve
            FROM bloomberg_tickers 
            WHERE currency_code = %s
        """, (currency,))
        
        total, with_curve, without_curve = cursor.fetchone()
        
        print(f"{currency}: {total:>3} total tickers, {with_curve:>2} in curves, {without_curve:>2} orphaned")
        
        if with_curve > 0:
            # Show curve breakdown
            cursor.execute("""
                SELECT curve_name, COUNT(*) as count
                FROM bloomberg_tickers 
                WHERE currency_code = %s AND curve_name IS NOT NULL
                GROUP BY curve_name
                ORDER BY count DESC
            """, (currency,))
            
            for curve_name, count in cursor.fetchall():
                print(f"    {curve_name}: {count} tickers")
    
    cursor.close()
    conn.close()

def check_gateway_response():
    """Check gateway API response for all G10 currencies"""
    print("\nGATEWAY API ANALYSIS")
    print("=" * 80)
    
    currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD', 'SEK', 'NOK']
    
    for currency in currencies:
        try:
            response = requests.post(
                f"{gateway_url}/api/curves/{currency}",
                headers={"Authorization": "Bearer test"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'points' in data:
                    points = data['points']
                    valid_points = [p for p in points if p.get('rate') is not None]
                    null_points = [p for p in points if p.get('rate') is None]
                    
                    print(f"{currency}: {len(points):>2} total, {len(valid_points):>2} valid, {len(null_points):>2} null rates")
                    
                    if null_points:
                        print(f"    Null rate tickers: {', '.join([p['ticker'] for p in null_points[:3]])}...")
                else:
                    print(f"{currency}: API error - {data}")
            else:
                print(f"{currency}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"{currency}: Connection error - {e}")
        
        time.sleep(0.5)  # Rate limiting

def check_missing_standard_tenors():
    """Check for missing standard tenors across all currencies"""
    print("\nMISSING STANDARD TENORS")
    print("=" * 80)
    
    # Standard tenors we expect for a complete curve
    standard_tenors = [
        ('O/N', 1), ('1W', 7), ('2W', 14), ('1M', 30), ('2M', 60), ('3M', 90),
        ('6M', 180), ('9M', 270), ('1Y', 365), ('18M', 548), ('2Y', 730),
        ('3Y', 1095), ('4Y', 1460), ('5Y', 1825), ('7Y', 2555), ('10Y', 3650),
        ('15Y', 5475), ('20Y', 7300), ('30Y', 9999)
    ]
    
    conn = psycopg2.connect(**conn_params)
    cursor = conn.cursor()
    
    currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD', 'SEK', 'NOK']
    
    for currency in currencies:
        cursor.execute("""
            SELECT tenor_numeric FROM bloomberg_tickers 
            WHERE currency_code = %s AND curve_name IS NOT NULL
            ORDER BY tenor_numeric
        """, (currency,))
        
        existing_tenors = {float(row[0]) for row in cursor.fetchall()}
        missing_tenors = []
        
        for tenor_name, days in standard_tenors:
            if days not in existing_tenors:
                missing_tenors.append(tenor_name)
        
        print(f"{currency}: Missing {len(missing_tenors)}/19 standard tenors")
        if missing_tenors:
            print(f"    {', '.join(missing_tenors[:10])}")
            if len(missing_tenors) > 10:
                print(f"    ... and {len(missing_tenors) - 10} more")
    
    cursor.close()
    conn.close()

def check_data_quality():
    """Check for data quality issues"""
    print("\nDATA QUALITY ISSUES")
    print("=" * 80)
    
    conn = psycopg2.connect(**conn_params)
    cursor = conn.cursor()
    
    # Check for duplicate tenor_numeric values within same currency
    cursor.execute("""
        SELECT currency_code, tenor_numeric, COUNT(*) as count, array_agg(bloomberg_ticker)
        FROM bloomberg_tickers 
        WHERE curve_name IS NOT NULL
        GROUP BY currency_code, tenor_numeric
        HAVING COUNT(*) > 1
        ORDER BY currency_code, tenor_numeric
    """)
    
    duplicates = cursor.fetchall()
    if duplicates:
        print("DUPLICATE TENORS FOUND:")
        for currency, tenor_numeric, count, tickers in duplicates:
            days = float(tenor_numeric)
            years = days / 365.0
            print(f"  {currency} {days:.0f}d ({years:.2f}Y): {count} tickers -> {tickers}")
    else:
        print("✓ No duplicate tenors found")
    
    # Check for unrealistic tenor_numeric values
    cursor.execute("""
        SELECT currency_code, bloomberg_ticker, tenor, tenor_numeric
        FROM bloomberg_tickers 
        WHERE curve_name IS NOT NULL AND (tenor_numeric < 0 OR tenor_numeric > 12000)
        ORDER BY currency_code, tenor_numeric
    """)
    
    unrealistic = cursor.fetchall()
    if unrealistic:
        print("\nUNREALISTIC TENOR VALUES:")
        for currency, ticker, tenor, tenor_numeric in unrealistic:
            print(f"  {currency} {ticker}: {tenor} -> {tenor_numeric} days")
    else:
        print("✓ No unrealistic tenor values found")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    print("SYSTEMATIC G10 CURRENCIES REVIEW")
    print("=" * 80)
    print()
    
    check_database_coverage()
    check_gateway_response() 
    check_missing_standard_tenors()
    check_data_quality()
    
    print("\n" + "=" * 80)
    print("REVIEW COMPLETE")