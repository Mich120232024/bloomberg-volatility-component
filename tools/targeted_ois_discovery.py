#!/usr/bin/env python3
"""
Targeted OIS Ticker Discovery and Database Population
Focus on currencies and patterns that actually work
Uses existing database schema and validates with real Bloomberg data
"""

import requests
import json
import time
import psycopg2
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('targeted_ois_discovery.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Bloomberg API Configuration
BLOOMBERG_API_URL = "http://20.172.249.92:8080"
HEADERS = {
    "Authorization": "Bearer test",
    "Content-Type": "application/json"
}

# Database Configuration
DB_CONFIG = {
    'host': 'gzcdevserver.postgres.database.azure.com',
    'database': 'gzc_platform',
    'user': 'mikael',
    'password': 'Ii89rra137+*',
    'port': 5432,
    'sslmode': 'require'
}

# Known OIS ticker patterns that work in Bloomberg
KNOWN_OIS_PATTERNS = {
    'USD': {
        'patterns': ['USSO', 'US SOFR'],
        'tenors': [1, 2, 3, 5, 7, 10, 15, 20, 30],  # Years
        'short_tenors': ['ON', '1W', '2W', '3W', '1M', '2M', '3M', '6M', '9M']  # Short end
    },
    'EUR': {
        'patterns': ['EUSO', 'EUROIS', 'EUR ESTR'],
        'tenors': [1, 2, 3, 5, 7, 10, 15, 20, 30],
        'short_tenors': ['ON', '1W', '2W', '3W', '1M', '2M', '3M', '6M', '9M']
    },
    'GBP': {
        'patterns': ['GBPSO', 'GBP SONIA', 'UKSO'],
        'tenors': [1, 2, 3, 5, 7, 10, 15, 20, 30],
        'short_tenors': ['ON', '1W', '2W', '3W', '1M', '2M', '3M', '6M', '9M']
    },
    'JPY': {
        'patterns': ['JPYSO', 'JPY TONAR', 'JYSO'],
        'tenors': [1, 2, 3, 5, 7, 10, 15, 20, 30],
        'short_tenors': ['ON', '1W', '2W', '3W', '1M', '2M', '3M', '6M', '9M']
    },
    'CHF': {
        'patterns': ['CHFSO', 'CHF SARON', 'SFSO'],
        'tenors': [1, 2, 3, 5, 7, 10, 15, 20, 30],
        'short_tenors': ['ON', '1W', '2W', '3W', '1M', '2M', '3M', '6M', '9M']
    },
    'CAD': {
        'patterns': ['CADSO', 'CAD CORRA', 'CDSO'],
        'tenors': [1, 2, 3, 5, 7, 10, 15, 20, 30],
        'short_tenors': ['ON', '1W', '2W', '3W', '1M', '2M', '3M', '6M', '9M']
    },
    'AUD': {
        'patterns': ['AUDSO', 'AUD AONIA', 'ADSO'],
        'tenors': [1, 2, 3, 5, 7, 10, 15, 20, 30],
        'short_tenors': ['ON', '1W', '2W', '3W', '1M', '2M', '3M', '6M', '9M']
    },
    'NZD': {
        'patterns': ['NZDSO', 'NZD OCR', 'NZSO'],
        'tenors': [1, 2, 3, 5, 7, 10, 15, 20, 30],
        'short_tenors': ['ON', '1W', '2W', '3W', '1M', '2M', '3M', '6M', '9M']
    },
    'SEK': {
        'patterns': ['SEKSO', 'SEK STINA', 'SESO'],
        'tenors': [1, 2, 3, 5, 7, 10, 15, 20, 30],
        'short_tenors': ['ON', '1W', '2W', '3W', '1M', '2M', '3M', '6M', '9M']
    },
    'NOK': {
        'patterns': ['NOKSO', 'NOK NOWA', 'NOSO'],
        'tenors': [1, 2, 3, 5, 7, 10, 15, 20, 30],
        'short_tenors': ['ON', '1W', '2W', '3W', '1M', '2M', '3M', '6M', '9M']
    }
}

class TargetedOISDiscovery:
    def __init__(self):
        self.valid_tickers = {}
        self.total_discovered = 0
        self.total_valid = 0
        
    def test_bloomberg_connection(self) -> bool:
        """Test Bloomberg API connection"""
        try:
            response = requests.get(f"{BLOOMBERG_API_URL}/health", timeout=10)
            if response.status_code == 200:
                logger.info("✅ Bloomberg API connection successful")
                return True
            else:
                logger.error(f"❌ Bloomberg API health check failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Failed to connect to Bloomberg API: {e}")
            return False
    
    def generate_ticker_candidates(self, currency: str) -> List[str]:
        """Generate comprehensive list of potential OIS tickers for a currency"""
        candidates = []
        
        if currency not in KNOWN_OIS_PATTERNS:
            logger.warning(f"No known patterns for {currency}")
            return candidates
        
        patterns = KNOWN_OIS_PATTERNS[currency]
        
        # Generate year-based tickers
        for pattern in patterns['patterns']:
            for tenor in patterns['tenors']:
                # Common formats
                candidates.extend([
                    f"{pattern}{tenor} Curncy",
                    f"{pattern}{tenor} Index",
                    f"{pattern}{tenor:02d} Curncy",  # Zero-padded
                    f"{pattern}0{tenor} Curncy" if tenor < 10 else f"{pattern}{tenor} Curncy",
                ])
        
        # Generate short-term tickers
        for pattern in patterns['patterns']:
            for tenor in patterns['short_tenors']:
                candidates.extend([
                    f"{pattern}{tenor} Curncy",
                    f"{pattern}{tenor} Index",
                ])
        
        # Remove duplicates
        return list(set(candidates))
    
    def validate_tickers_bulk(self, tickers: List[str]) -> Dict[str, bool]:
        """Validate multiple tickers efficiently using Bloomberg reference data"""
        if not tickers:
            return {}
            
        logger.info(f"🔍 Validating {len(tickers)} ticker candidates")
        
        validation_results = {}
        chunk_size = 20  # Conservative chunk size
        
        for i in range(0, len(tickers), chunk_size):
            chunk = tickers[i:i + chunk_size]
            
            try:
                response = requests.post(
                    f"{BLOOMBERG_API_URL}/api/bloomberg/reference",
                    headers=HEADERS,
                    json={
                        "securities": chunk,
                        "fields": ["PX_LAST", "SECURITY_NAME", "SECURITY_DES"]
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        for sec_data in data.get("data", {}).get("securities_data", []):
                            ticker = sec_data.get("security")
                            is_valid = sec_data.get("success", False) and sec_data.get("fields", {}).get("PX_LAST") is not None
                            validation_results[ticker] = is_valid
                            
                            if is_valid:
                                price = sec_data.get("fields", {}).get("PX_LAST")
                                name = sec_data.get("fields", {}).get("SECURITY_NAME", "")
                                logger.info(f"  ✅ {ticker} = {price} ({name})")
                            else:
                                logger.debug(f"  ❌ {ticker} - No data")
                    else:
                        logger.error(f"Reference data request failed: {data.get('error', 'Unknown error')}")
                else:
                    logger.error(f"Reference data API error: {response.status_code}")
            
            except Exception as e:
                logger.error(f"Error validating chunk: {e}")
                for ticker in chunk:
                    validation_results[ticker] = False
            
            time.sleep(1)  # Rate limiting
        
        valid_count = sum(1 for v in validation_results.values() if v)
        logger.info(f"📊 Validation complete: {valid_count}/{len(tickers)} valid")
        
        return validation_results
    
    def connect_to_database(self):
        """Connect to PostgreSQL database"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            logger.info("✅ Connected to PostgreSQL database")
            return conn
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            return None
    
    def insert_valid_tickers(self, conn, currency: str, valid_tickers: Dict[str, bool]):
        """Insert valid tickers into database using existing schema"""
        inserted_count = 0
        skipped_count = 0
        
        try:
            with conn.cursor() as cursor:
                for ticker, is_valid in valid_tickers.items():
                    if not is_valid:
                        skipped_count += 1
                        continue
                    
                    # Determine curve name
                    curve_name = f"{currency}_OIS"
                    
                    # Insert or update ticker (using existing schema)
                    cursor.execute("""
                        INSERT INTO ticker_reference 
                        (bloomberg_ticker, currency_code, instrument_type, curve_name, is_active)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (bloomberg_ticker) 
                        DO UPDATE SET 
                            currency_code = EXCLUDED.currency_code,
                            instrument_type = EXCLUDED.instrument_type,
                            curve_name = EXCLUDED.curve_name,
                            is_active = EXCLUDED.is_active
                    """, (ticker, currency, 'OIS', curve_name, True))
                    
                    inserted_count += 1
                
                conn.commit()
                logger.info(f"✅ Inserted/updated {inserted_count} tickers for {currency}")
                
        except Exception as e:
            logger.error(f"❌ Failed to insert tickers for {currency}: {e}")
            conn.rollback()
    
    def discover_currency_ois(self, currency: str, conn) -> int:
        """Discover and validate OIS tickers for a specific currency"""
        logger.info(f"\n{'='*50}")
        logger.info(f"Discovering OIS tickers for {currency}")
        logger.info(f"{'='*50}")
        
        # Generate ticker candidates
        candidates = self.generate_ticker_candidates(currency)
        if not candidates:
            logger.warning(f"No ticker candidates generated for {currency}")
            return 0
        
        logger.info(f"Generated {len(candidates)} ticker candidates")
        
        # Validate candidates
        validation_results = self.validate_tickers_bulk(candidates)
        if not validation_results:
            logger.warning(f"Validation failed for {currency}")
            return 0
        
        # Count valid tickers
        valid_count = sum(1 for v in validation_results.values() if v)
        
        if valid_count > 0:
            logger.info(f"🎉 Found {valid_count} valid OIS tickers for {currency}")
            
            # Store results
            self.valid_tickers[currency] = {
                ticker: is_valid 
                for ticker, is_valid in validation_results.items() 
                if is_valid
            }
            
            # Insert into database
            self.insert_valid_tickers(conn, currency, validation_results)
        else:
            logger.warning(f"⚠️  No valid OIS tickers found for {currency}")
        
        return valid_count
    
    def discover_all_ois_tickers(self):
        """Main method to discover OIS tickers for all currencies"""
        logger.info("🚀 Starting targeted OIS ticker discovery")
        logger.info("Focus: Finding REAL OIS tickers that exist in Bloomberg")
        
        # Test Bloomberg connection
        if not self.test_bloomberg_connection():
            logger.error("❌ Cannot proceed without Bloomberg API connection")
            return
        
        # Connect to database
        conn = self.connect_to_database()
        if not conn:
            logger.error("❌ Cannot proceed without database connection")
            return
        
        try:
            # Process all currencies with known patterns
            currencies = list(KNOWN_OIS_PATTERNS.keys())
            logger.info(f"Processing {len(currencies)} currencies: {', '.join(currencies)}")
            
            for currency in currencies:
                valid_count = self.discover_currency_ois(currency, conn)
                self.total_valid += valid_count
                time.sleep(2)  # Rate limiting between currencies
            
            # Generate final report
            self.generate_final_report()
            
        finally:
            conn.close()
            logger.info("✅ Database connection closed")
    
    def generate_final_report(self):
        """Generate comprehensive final report"""
        logger.info(f"\n{'='*60}")
        logger.info("TARGETED OIS DISCOVERY - FINAL REPORT")
        logger.info(f"{'='*60}")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_currencies_processed': len(self.valid_tickers),
            'total_valid_tickers': self.total_valid,
            'currencies_with_ois': {},
            'currencies_without_ois': [],
            'summary': {}
        }
        
        for currency in KNOWN_OIS_PATTERNS.keys():
            if currency in self.valid_tickers and self.valid_tickers[currency]:
                valid_tickers = list(self.valid_tickers[currency].keys())
                report['currencies_with_ois'][currency] = {
                    'ticker_count': len(valid_tickers),
                    'tickers': valid_tickers
                }
                logger.info(f"✅ {currency}: {len(valid_tickers)} valid OIS tickers")
                for ticker in valid_tickers[:5]:  # Show first 5
                    logger.info(f"    {ticker}")
                if len(valid_tickers) > 5:
                    logger.info(f"    ... and {len(valid_tickers) - 5} more")
            else:
                report['currencies_without_ois'].append(currency)
                logger.info(f"❌ {currency}: No valid OIS tickers found")
        
        # Summary statistics
        report['summary'] = {
            'currencies_with_ois': len(report['currencies_with_ois']),
            'currencies_without_ois': len(report['currencies_without_ois']),
            'total_valid_tickers': self.total_valid,
            'success_rate': f"{(len(report['currencies_with_ois']) / len(KNOWN_OIS_PATTERNS) * 100):.1f}%"
        }
        
        logger.info(f"\n📊 SUMMARY:")
        logger.info(f"  Currencies with OIS: {report['summary']['currencies_with_ois']}")
        logger.info(f"  Currencies without OIS: {report['summary']['currencies_without_ois']}")
        logger.info(f"  Total valid tickers: {report['summary']['total_valid_tickers']}")
        logger.info(f"  Success rate: {report['summary']['success_rate']}")
        
        # Save reports
        with open('targeted_ois_discovery_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        with open('valid_ois_tickers.json', 'w') as f:
            json.dump(self.valid_tickers, f, indent=2)
        
        logger.info(f"\n📁 Reports saved:")
        logger.info(f"  - targeted_ois_discovery_report.json")
        logger.info(f"  - valid_ois_tickers.json")
        logger.info(f"  - targeted_ois_discovery.log")
        
        # Database summary
        logger.info(f"\n💾 DATABASE POPULATED:")
        logger.info(f"  Table: ticker_reference")
        logger.info(f"  Records added/updated: {self.total_valid}")
        logger.info(f"  Instrument type: OIS")

def main():
    """Main execution function"""
    discovery = TargetedOISDiscovery()
    discovery.discover_all_ois_tickers()

if __name__ == "__main__":
    main()