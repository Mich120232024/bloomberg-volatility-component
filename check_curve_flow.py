#!/usr/bin/env python3
"""
CHECK CURVE FLOW - Database to Bloomberg API
Verifies the complete flow: PostgreSQL curve members → Bloomberg API → yield curve data
"""

import os
import psycopg2
import requests
import json
from datetime import datetime

def get_curve_tickers(curve_name):
    """Get tickers for a specific curve from database"""
    conn_str = os.getenv('POSTGRES_CONNECTION_STRING')
    if not conn_str:
        print("❌ No POSTGRES_CONNECTION_STRING found")
        return []
    
    # Remove asyncpg prefix for psycopg2 compatibility
    if conn_str.startswith('postgresql+asyncpg://'):
        conn_str = conn_str.replace('postgresql+asyncpg://', 'postgresql://')
        
    try:
        conn = psycopg2.connect(conn_str)
        cursor = conn.cursor()
        
        # Query curve members with ticker details using curve_memberships
        query = """
            SELECT 
                bt.bloomberg_ticker,
                bt.properties->>'tenor' as tenor,
                bt.properties->>'years' as years,
                bt.properties->>'label' as label,
                bt.properties->>'sorting_order' as sort_order,
                bt.category,
                bt.subcategory,
                bt.properties
            FROM bloomberg_tickers bt
            WHERE bt.properties->'curve_memberships' ? %s
            ORDER BY CAST(COALESCE(bt.properties->>'sorting_order', '0') AS INTEGER)
        """
        
        cursor.execute(query, [curve_name])
        results = cursor.fetchall()
        
        tickers = []
        for row in results:
            ticker, tenor, years, label, sort_order, category, subcategory, properties = row
            print(f"   DEBUG: {ticker} properties: {properties}")
            tickers.append({
                'ticker': ticker,
                'tenor': tenor,
                'years': float(years) if years else 0,
                'label': label,
                'sort_order': int(sort_order) if sort_order else 0,
                'category': category,
                'subcategory': subcategory
            })
        
        cursor.close()
        conn.close()
        return tickers
        
    except Exception as e:
        print(f"❌ Database query failed: {e}")
        return []

def call_bloomberg_api(tickers):
    """Call Bloomberg API for ticker rates"""
    bloomberg_tickers = [t['ticker'] for t in tickers]
    fields = ['PX_LAST', 'YLD_YTM_MID', 'LAST_UPDATE']
    
    payload = {
        "securities": bloomberg_tickers,
        "fields": fields
    }
    
    try:
        response = requests.post(
            "http://20.172.249.92:8080/api/bloomberg/reference",
            headers={
                'Authorization': 'Bearer test',
                'Content-Type': 'application/json'
            },
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        return response.json()
        
    except Exception as e:
        print(f"❌ Bloomberg API call failed: {e}")
        return {"success": False, "error": str(e)}

def debug_database():
    """Debug database connection and structure"""
    conn_str = os.getenv('POSTGRES_CONNECTION_STRING')
    if not conn_str:
        print("❌ No POSTGRES_CONNECTION_STRING found")
        return []
    
    # Remove asyncpg prefix for psycopg2 compatibility
    if conn_str.startswith('postgresql+asyncpg://'):
        conn_str = conn_str.replace('postgresql+asyncpg://', 'postgresql://')
        
    try:
        conn = psycopg2.connect(conn_str)
        cursor = conn.cursor()
        
        # Check table exists
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name LIKE '%ticker%'
        """)
        tables = cursor.fetchall()
        print(f"📊 Tables found: {tables}")
        
        # Check bloomberg_tickers structure
        cursor.execute("SELECT COUNT(*) FROM bloomberg_tickers")
        count = cursor.fetchone()[0]
        print(f"📊 Total tickers: {count}")
        
        # Check a few sample records
        cursor.execute("""
            SELECT bloomberg_ticker, currency_code, category, properties 
            FROM bloomberg_tickers 
            LIMIT 5
        """)
        samples = cursor.fetchall()
        print(f"📊 Sample records:")
        for ticker, curr, cat, props in samples:
            print(f"   {ticker} | {curr} | {cat} | {type(props)} {str(props)[:100]}...")
            
        # Check for properties with curve_memberships
        cursor.execute("""
            SELECT COUNT(*) FROM bloomberg_tickers 
            WHERE properties IS NOT NULL AND properties::text LIKE '%curve_memberships%'
        """)
        curve_count = cursor.fetchone()[0]
        print(f"📊 Records with 'curve_memberships' in properties: {curve_count}")
        
        # Get available curve names
        cursor.execute("""
            SELECT DISTINCT jsonb_array_elements_text(properties->'curve_memberships') as curve_name,
                   COUNT(*) as ticker_count
            FROM bloomberg_tickers 
            WHERE properties ? 'curve_memberships' 
            GROUP BY curve_name
            ORDER BY ticker_count DESC
            LIMIT 10
        """)
        curves = cursor.fetchall()
        print(f"📊 Available curves:")
        for curve, count in curves:
            print(f"   {curve}: {count} tickers")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database debug failed: {e}")
        return False

def check_curve_flow(curve_name="JPY_OIS"):
    """Check complete flow for a curve"""
    print(f"🔍 CHECKING CURVE FLOW: {curve_name}")
    print("=" * 60)
    
    # Step 1: Get tickers from database
    print(f"\n📊 Step 1: Querying database for curve members...")
    tickers = get_curve_tickers(curve_name)
    
    if not tickers:
        print(f"❌ No tickers found for curve {curve_name}")
        return False
    
    print(f"✅ Found {len(tickers)} tickers for {curve_name}:")
    for ticker in tickers:
        print(f"   {ticker['ticker']} | {ticker['label']} | {ticker['years']}Y | {ticker['category']}")
    
    # Step 2: Call Bloomberg API
    print(f"\n📡 Step 2: Calling Bloomberg API for {len(tickers)} tickers...")
    api_result = call_bloomberg_api(tickers)
    
    if not api_result.get('success'):
        print(f"❌ Bloomberg API failed: {api_result.get('error')}")
        return False
    
    # Step 3: Process results
    print("✅ Bloomberg API successful!")
    securities_data = api_result.get('data', {}).get('securities_data', [])
    
    print(f"\n📈 Step 3: Processing {len(securities_data)} responses...")
    curve_points = []
    
    for i, sec_data in enumerate(securities_data):
        if i < len(tickers):
            ticker_info = tickers[i]
            
            if sec_data.get('success'):
                fields = sec_data.get('fields', {})
                rate = fields.get('YLD_YTM_MID') or fields.get('PX_LAST')
                
                if rate is not None:
                    curve_points.append({
                        'ticker': ticker_info['ticker'],
                        'label': ticker_info['label'],
                        'years': ticker_info['years'],
                        'rate': rate,
                        'category': ticker_info['category']
                    })
                    print(f"   ✅ {ticker_info['ticker']}: {rate}% ({ticker_info['label']})")
                else:
                    print(f"   ⚠️ {ticker_info['ticker']}: No rate data")
            else:
                print(f"   ❌ {ticker_info['ticker']}: {sec_data.get('error', 'Unknown error')}")
    
    # Step 4: Summary
    print(f"\n🎯 FLOW CHECK RESULTS:")
    print(f"   Database tickers: {len(tickers)}")
    print(f"   API responses: {len(securities_data)}")
    print(f"   Valid curve points: {len(curve_points)}")
    print(f"   Success rate: {len(curve_points)/len(tickers)*100:.1f}%")
    
    if curve_points:
        print(f"\n📊 YIELD CURVE CONSTRUCTION READY:")
        curve_points.sort(key=lambda x: x['years'])
        for point in curve_points:
            print(f"   {point['years']:>6.3f}Y: {point['rate']:>6.3f}% | {point['ticker']}")
    
    return len(curve_points) > 0

if __name__ == "__main__":
    print("🔍 DATABASE DEBUG")
    print("=" * 40)
    debug_database()
    
    print("\n🔍 CURVE FLOW CHECK")
    print("=" * 40)
    success = check_curve_flow("JPY_OIS")
    
    if success:
        print(f"\n🎉 CURVE FLOW CHECK PASSED")
        print("   Database → Bloomberg API → Yield Curve: WORKING")
    else:
        print(f"\n❌ CURVE FLOW CHECK FAILED")
        print("   Check database connection and Bloomberg API availability")