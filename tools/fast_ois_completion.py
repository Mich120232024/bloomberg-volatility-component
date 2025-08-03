#!/usr/bin/env python3
"""
Fast OIS Completion Script
Complete the discovery for remaining currencies and generate final report
"""

import requests
import json
import time
import psycopg2
import logging
from typing import Dict, List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Bloomberg API Configuration
BLOOMBERG_API_URL = "http://20.172.249.92:8080"
HEADERS = {"Authorization": "Bearer test", "Content-Type": "application/json"}

# Database Configuration
DB_CONFIG = {
    'host': 'gzcdevserver.postgres.database.azure.com',
    'database': 'gzc_platform',
    'user': 'mikael',
    'password': 'Ii89rra137+*',
    'port': 5432,
    'sslmode': 'require'
}

# Focus on currencies that likely have OIS
PRIORITY_CURRENCIES = ['NZD', 'SEK', 'NOK', 'CHF', 'JPY']

# Known working patterns from partial run
WORKING_PATTERNS = {
    'NZD': ['NZSO', 'NZD OCR'],
    'SEK': ['SESO', 'SEK STINA'], 
    'NOK': ['NOSO', 'NOK NOWA'],
    'CHF': ['SFSO', 'CHF SARON'],
    'JPY': ['JPYSO', 'JPY TONAR']
}

def validate_ticker_set(tickers: List[str]) -> Dict[str, bool]:
    """Validate a set of tickers quickly"""
    validation_results = {}
    chunk_size = 15
    
    for i in range(0, len(tickers), chunk_size):
        chunk = tickers[i:i + chunk_size]
        
        try:
            response = requests.post(
                f"{BLOOMBERG_API_URL}/api/bloomberg/reference",
                headers=HEADERS,
                json={"securities": chunk, "fields": ["PX_LAST"]},
                timeout=20
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    for sec_data in data.get("data", {}).get("securities_data", []):
                        ticker = sec_data.get("security")
                        is_valid = (sec_data.get("success", False) and 
                                  sec_data.get("fields", {}).get("PX_LAST") is not None)
                        validation_results[ticker] = is_valid
                        if is_valid:
                            price = sec_data.get("fields", {}).get("PX_LAST")
                            logger.info(f"✅ {ticker} = {price}")
        except Exception as e:
            logger.error(f"Validation error: {e}")
            for ticker in chunk:
                validation_results[ticker] = False
        
        time.sleep(0.5)
    
    return validation_results

def generate_currency_candidates(currency: str) -> List[str]:
    """Generate focused ticker candidates"""
    candidates = []
    
    if currency in WORKING_PATTERNS:
        patterns = WORKING_PATTERNS[currency]
        tenors = [1, 2, 3, 5, 7, 10, 15, 20, 30]  # Standard tenors
        
        for pattern in patterns:
            for tenor in tenors:
                candidates.extend([
                    f"{pattern}{tenor} Curncy",
                    f"{pattern}{tenor} Index"
                ])
    
    return list(set(candidates))

def insert_tickers_to_db(currency: str, valid_tickers: Dict[str, bool]) -> int:
    """Insert valid tickers to database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        inserted = 0
        
        with conn.cursor() as cursor:
            for ticker, is_valid in valid_tickers.items():
                if is_valid:
                    cursor.execute("""
                        INSERT INTO ticker_reference 
                        (bloomberg_ticker, currency_code, instrument_type, curve_name, is_active)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (bloomberg_ticker) 
                        DO UPDATE SET is_active = EXCLUDED.is_active
                    """, (ticker, currency, 'OIS', f"{currency}_OIS", True))
                    inserted += 1
        
        conn.commit()
        conn.close()
        logger.info(f"✅ Inserted {inserted} tickers for {currency}")
        return inserted
        
    except Exception as e:
        logger.error(f"❌ Database error for {currency}: {e}")
        return 0

def discover_currency_fast(currency: str) -> int:
    """Fast discovery for a single currency"""
    logger.info(f"\n🔍 Fast discovery: {currency}")
    
    candidates = generate_currency_candidates(currency)
    if not candidates:
        logger.warning(f"No candidates for {currency}")
        return 0
    
    logger.info(f"Validating {len(candidates)} candidates")
    validation_results = validate_ticker_set(candidates)
    
    valid_count = sum(1 for v in validation_results.values() if v)
    logger.info(f"Found {valid_count} valid tickers")
    
    if valid_count > 0:
        inserted = insert_tickers_to_db(currency, validation_results)
        return inserted
    
    return 0

def check_current_database_status():
    """Check what's already in the database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT currency_code, COUNT(*) 
                FROM ticker_reference 
                WHERE instrument_type = 'OIS' AND is_active = true
                GROUP BY currency_code 
                ORDER BY currency_code
            """)
            results = cursor.fetchall()
        
        conn.close()
        
        logger.info("📊 Current OIS tickers in database:")
        total = 0
        for currency, count in results:
            logger.info(f"  {currency}: {count} tickers")
            total += count
        logger.info(f"  TOTAL: {total} OIS tickers")
        
        return dict(results)
        
    except Exception as e:
        logger.error(f"Database check error: {e}")
        return {}

def main():
    """Main execution"""
    logger.info("🚀 Fast OIS Discovery Completion")
    
    # Check current status
    current_status = check_current_database_status()
    
    # Process remaining currencies
    total_new = 0
    for currency in PRIORITY_CURRENCIES:
        if currency not in current_status or current_status[currency] < 5:
            new_count = discover_currency_fast(currency)
            total_new += new_count
            time.sleep(1)
        else:
            logger.info(f"✅ {currency} already has {current_status[currency]} tickers")
    
    # Final status check
    logger.info(f"\n🎉 Discovery completion:")
    logger.info(f"  New tickers added: {total_new}")
    
    final_status = check_current_database_status()
    
    # Generate summary
    summary = {
        'timestamp': datetime.now().isoformat(),
        'currencies_with_ois': final_status,
        'total_ois_tickers': sum(final_status.values()),
        'currencies_covered': len(final_status)
    }
    
    with open('final_ois_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info("✅ Summary saved to final_ois_summary.json")

if __name__ == "__main__":
    main()