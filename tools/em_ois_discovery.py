#!/usr/bin/env python3
"""
Emerging Market OIS Ticker Discovery
Attempt to find OIS tickers for EM currencies
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

# EM currencies to try
EM_CURRENCIES = ['MXN', 'ZAR', 'TRY', 'CNH', 'INR', 'KRW', 'TWD', 'SGD', 'HKD', 'THB', 'ILS', 'PLN', 'CZK', 'HUF', 'RUB', 'PHP', 'DKK', 'BRL']

def test_em_patterns(currency: str) -> List[str]:
    """Test common EM OIS patterns"""
    candidates = []
    
    # Common patterns
    patterns = [
        f"{currency}SO",    # Standard OIS
        f"{currency}OIS",   # Explicit OIS
        f"{currency}SW",    # Swap
        f"{currency}IR"     # Interest Rate
    ]
    
    tenors = [1, 2, 3, 5, 7, 10]  # Limited tenors for EM
    
    for pattern in patterns:
        for tenor in tenors:
            candidates.extend([
                f"{pattern}{tenor} Curncy",
                f"{pattern}{tenor} Index"
            ])
    
    return candidates

def validate_em_tickers(currency: str, candidates: List[str]) -> Dict[str, bool]:
    """Validate EM ticker candidates"""
    validation_results = {}
    
    try:
        # Try smaller chunks for EM
        chunk_size = 10
        for i in range(0, len(candidates), chunk_size):
            chunk = candidates[i:i + chunk_size]
            
            response = requests.post(
                f"{BLOOMBERG_API_URL}/api/bloomberg/reference",
                headers=HEADERS,
                json={"securities": chunk, "fields": ["PX_LAST"]},
                timeout=15
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
            
            time.sleep(0.8)  # Conservative rate limiting
            
    except Exception as e:
        logger.error(f"Validation error for {currency}: {e}")
    
    return validation_results

def discover_em_currency(currency: str) -> int:
    """Discover OIS tickers for an EM currency"""
    logger.info(f"\n🔍 EM Discovery: {currency}")
    
    candidates = test_em_patterns(currency)
    logger.info(f"Testing {len(candidates)} candidates")
    
    validation_results = validate_em_tickers(currency, candidates)
    valid_count = sum(1 for v in validation_results.values() if v)
    
    if valid_count > 0:
        logger.info(f"🎉 Found {valid_count} valid tickers for {currency}")
        # Insert to database
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            with conn.cursor() as cursor:
                for ticker, is_valid in validation_results.items():
                    if is_valid:
                        cursor.execute("""
                            INSERT INTO ticker_reference 
                            (bloomberg_ticker, currency_code, instrument_type, curve_name, is_active)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (bloomberg_ticker) 
                            DO UPDATE SET is_active = EXCLUDED.is_active
                        """, (ticker, currency, 'OIS', f"{currency}_OIS", True))
            conn.commit()
            conn.close()
            logger.info(f"✅ Inserted {valid_count} tickers for {currency}")
        except Exception as e:
            logger.error(f"Database error for {currency}: {e}")
    else:
        logger.info(f"❌ No valid OIS tickers found for {currency}")
    
    return valid_count

def main():
    """Main EM discovery"""
    logger.info("🚀 Emerging Market OIS Discovery")
    
    em_results = {}
    total_em_found = 0
    
    for currency in EM_CURRENCIES:
        found = discover_em_currency(currency)
        em_results[currency] = found
        total_em_found += found
        time.sleep(1)
    
    # Final summary
    logger.info(f"\n📊 EM OIS Discovery Results:")
    for currency, count in em_results.items():
        if count > 0:
            logger.info(f"✅ {currency}: {count} OIS tickers")
        else:
            logger.info(f"❌ {currency}: No OIS tickers")
    
    logger.info(f"\nTotal EM OIS tickers found: {total_em_found}")
    
    # Save EM results
    em_summary = {
        'timestamp': datetime.now().isoformat(),
        'em_currencies_tested': EM_CURRENCIES,
        'results': em_results,
        'total_em_tickers': total_em_found,
        'currencies_with_ois': [c for c, count in em_results.items() if count > 0]
    }
    
    with open('em_ois_discovery_results.json', 'w') as f:
        json.dump(em_summary, f, indent=2)
    
    logger.info("✅ EM results saved to em_ois_discovery_results.json")

if __name__ == "__main__":
    main()