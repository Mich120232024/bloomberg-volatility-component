#!/usr/bin/env python3
"""
Efficient OIS Ticker Discovery and Database Population
Discovers and validates real OIS tickers for ALL currencies using Bloomberg API
Uses reference data endpoint for validation since validate-tickers doesn't exist
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
        logging.FileHandler('efficient_ois_discovery.log'),
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

# All currencies to discover
ALL_CURRENCIES = {
    # G10 currencies - highest priority
    'G10': ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD', 'SEK', 'NOK'],
    # Emerging Market currencies
    'EM': ['MXN', 'ZAR', 'TRY', 'CNH', 'INR', 'KRW', 'TWD', 'SGD', 'HKD', 'THB', 
           'ILS', 'PLN', 'CZK', 'HUF', 'RUB', 'PHP', 'DKK', 'BRL']
}

# Standard OIS tenors to try to find
STANDARD_TENORS = ['ON', '1W', '2W', '3W', '1M', '2M', '3M', '6M', '9M', '1Y', '18M', '2Y', '3Y', '4Y', '5Y', '7Y', '10Y', '15Y', '20Y', '30Y']

class EfficientOISDiscovery:
    def __init__(self):
        self.discovered_tickers = {}
        self.validated_tickers = {}
        self.failed_validations = {}
        
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
    
    def discover_currency_tickers(self, currency: str) -> List[Dict]:
        """Discover OIS tickers for a specific currency using focused search patterns"""
        logger.info(f"🔍 Discovering OIS tickers for {currency}")
        
        try:
            # Focus on the most effective search patterns
            search_patterns = [
                {"search_type": "ois", "currency": currency, "max_results": 100}
            ]
            
            all_tickers = []
            
            for pattern in search_patterns:
                try:
                    response = requests.post(
                        f"{BLOOMBERG_API_URL}/api/bloomberg/ticker-discovery",
                        headers=HEADERS,
                        json=pattern,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        tickers = data.get("tickers", [])
                        if tickers:
                            logger.info(f"  ✅ Found {len(tickers)} tickers")
                            all_tickers.extend(tickers)
                        else:
                            logger.info(f"  ⚠️  No tickers found with OIS search")
                    else:
                        logger.warning(f"  ❌ HTTP {response.status_code}")
                        
                    time.sleep(1)  # Rate limiting
                    
                except Exception as e:
                    logger.warning(f"  ❌ Search failed: {e}")
                    continue
            
            # If no tickers found with OIS search, try common patterns manually
            if not all_tickers:
                logger.info(f"  Trying manual pattern generation for {currency}")
                manual_tickers = self.generate_manual_ois_patterns(currency)
                all_tickers.extend(manual_tickers)
            
            # Remove duplicates
            unique_tickers = []
            seen_tickers = set()
            for ticker in all_tickers:
                ticker_code = ticker.get('ticker', '')
                if ticker_code and ticker_code not in seen_tickers:
                    unique_tickers.append(ticker)
                    seen_tickers.add(ticker_code)
            
            logger.info(f"✅ Found {len(unique_tickers)} total tickers for {currency}")
            
            # Filter for OIS-relevant tickers
            ois_tickers = []
            for ticker in unique_tickers:
                ticker_code = ticker.get('ticker', '')
                description = ticker.get('description', '')
                
                if self.is_ois_ticker(ticker_code, description, currency):
                    ois_tickers.append(ticker)
                    logger.info(f"    OIS: {ticker_code} - {description}")
            
            logger.info(f"✅ Filtered to {len(ois_tickers)} OIS-relevant tickers for {currency}")
            return ois_tickers
            
        except Exception as e:
            logger.error(f"❌ Error discovering {currency} tickers: {e}")
            return []
    
    def generate_manual_ois_patterns(self, currency: str) -> List[Dict]:
        """Generate manual OIS ticker patterns when discovery fails"""
        manual_patterns = []
        
        # Common OIS patterns by currency
        if currency == 'USD':
            base_patterns = ['USSO', 'USSOFR', 'USD SOFR']
        elif currency == 'EUR':
            base_patterns = ['EURSO', 'EURESTR', 'EUR ESTR']
        elif currency == 'GBP':
            base_patterns = ['GBPSO', 'GBPSONIA', 'GBP SONIA']
        elif currency == 'JPY':
            base_patterns = ['JPYSO', 'JPYTONAR', 'JPY TONAR']
        else:
            base_patterns = [f'{currency}SO', f'{currency}OIS']
        
        # Generate tickers for standard tenors
        for pattern in base_patterns:
            for tenor_num in [1, 2, 3, 5, 7, 10, 15, 20, 30]:  # Common year tenors
                ticker = f"{pattern}{tenor_num} Curncy"
                manual_patterns.append({
                    'ticker': ticker,
                    'description': f'{currency} OIS {tenor_num}Y',
                    'tenor': f'{tenor_num}Y'
                })
        
        logger.info(f"  Generated {len(manual_patterns)} manual patterns for {currency}")
        return manual_patterns
    
    def is_ois_ticker(self, ticker: str, description: str, currency: str) -> bool:
        """Determine if a ticker is OIS-related"""
        ticker_upper = ticker.upper()
        desc_upper = description.upper()
        
        # Explicit OIS indicators
        ois_indicators = [
            'OIS', 'OVERNIGHT', 'INDEX SWAP', 'SONIA', 'SOFR', 'ESTR', 'TONAR',
            'EONIA', 'ESTER', 'RFR', 'DAILY COMPOUNDED'
        ]
        
        # Check description
        if any(indicator in desc_upper for indicator in ois_indicators):
            return True
        
        # Check ticker patterns
        if f'{currency}SO' in ticker_upper:  # Common OIS pattern
            return True
        
        # Currency-specific patterns
        if currency == 'USD' and 'SOFR' in ticker_upper:
            return True
        elif currency == 'GBP' and 'SONIA' in ticker_upper:
            return True
        elif currency == 'EUR' and any(x in ticker_upper for x in ['ESTR', 'EONIA']):
            return True
        elif currency == 'JPY' and 'TONAR' in ticker_upper:
            return True
        
        return False
    
    def validate_tickers_with_reference_data(self, tickers: List[str]) -> Dict[str, bool]:
        """Validate tickers using Bloomberg reference data endpoint"""
        if not tickers:
            return {}
            
        logger.info(f"🔍 Validating {len(tickers)} tickers using reference data")
        
        try:
            # Validate in chunks of 10 to respect API limits
            chunk_size = 10
            validation_results = {}
            
            for i in range(0, len(tickers), chunk_size):
                chunk = tickers[i:i + chunk_size]
                
                try:
                    response = requests.post(
                        f"{BLOOMBERG_API_URL}/api/bloomberg/reference",
                        headers=HEADERS,
                        json={
                            "securities": chunk,
                            "fields": ["PX_LAST", "SECURITY_NAME"]
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("success"):
                            for sec_data in data.get("data", {}).get("securities_data", []):
                                ticker = sec_data.get("security")
                                is_valid = sec_data.get("success", False)
                                validation_results[ticker] = is_valid
                                
                                if is_valid:
                                    logger.info(f"  ✅ {ticker} - Valid")
                                else:
                                    logger.warning(f"  ❌ {ticker} - Invalid")
                        else:
                            logger.error(f"Reference data request failed: {data.get('error', 'Unknown error')}")
                    else:
                        logger.error(f"Reference data API error: {response.status_code}")
                
                except Exception as e:
                    logger.error(f"Error validating chunk: {e}")
                    # Mark all tickers in chunk as invalid
                    for ticker in chunk:
                        validation_results[ticker] = False
                
                time.sleep(2)  # Rate limiting between chunks
            
            return validation_results
            
        except Exception as e:
            logger.error(f"❌ Error validating tickers: {e}")
            return {}
    
    def connect_to_database(self):
        """Connect to PostgreSQL database"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            logger.info("✅ Connected to PostgreSQL database")
            return conn
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            return None
    
    def ensure_table_exists(self, conn):
        """Ensure ticker_reference table exists with proper schema"""
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ticker_reference (
                        id SERIAL PRIMARY KEY,
                        bloomberg_ticker VARCHAR(50) UNIQUE NOT NULL,
                        currency_code VARCHAR(3) NOT NULL,
                        instrument_type VARCHAR(20) DEFAULT 'OIS',
                        curve_name VARCHAR(50),
                        tenor VARCHAR(10),
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                logger.info("✅ Ensured ticker_reference table exists")
        except Exception as e:
            logger.error(f"❌ Failed to create table: {e}")
            conn.rollback()
    
    def insert_validated_tickers(self, conn, currency: str, validated_tickers: Dict[str, bool]):
        """Insert validated tickers into database"""
        inserted_count = 0
        skipped_count = 0
        
        try:
            with conn.cursor() as cursor:
                for ticker, is_valid in validated_tickers.items():
                    if not is_valid:
                        skipped_count += 1
                        continue
                    
                    # Determine curve name and tenor
                    curve_name = f"{currency}_OIS"
                    tenor = self.extract_tenor_from_ticker(ticker, currency)
                    
                    # Insert or update ticker
                    cursor.execute("""
                        INSERT INTO ticker_reference 
                        (bloomberg_ticker, currency_code, instrument_type, curve_name, tenor, is_active)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (bloomberg_ticker) 
                        DO UPDATE SET 
                            updated_at = CURRENT_TIMESTAMP,
                            is_active = EXCLUDED.is_active,
                            curve_name = EXCLUDED.curve_name,
                            tenor = EXCLUDED.tenor
                    """, (ticker, currency, 'OIS', curve_name, tenor, True))
                    
                    inserted_count += 1
                
                conn.commit()
                logger.info(f"✅ Inserted/updated {inserted_count} tickers for {currency}, skipped {skipped_count} invalid")
                
        except Exception as e:
            logger.error(f"❌ Failed to insert tickers for {currency}: {e}")
            conn.rollback()
    
    def extract_tenor_from_ticker(self, ticker: str, currency: str) -> Optional[str]:
        """Extract tenor from ticker code"""
        import re
        
        ticker_upper = ticker.upper()
        
        # Overnight patterns
        if any(pattern in ticker_upper for pattern in ['ON', 'O/N', 'OVERNIGHT']):
            return 'ON'
        
        # Common OIS patterns: USSO1, EURSO2, etc.
        ois_match = re.search(f'{currency}SO(\\d+)', ticker_upper)
        if ois_match:
            num = int(ois_match.group(1))
            if num <= 24:  # Up to 24 months
                return f"{num}M"
            else:
                return f"{num}Y"
        
        # Generic patterns: USD1Y, EUR6M, etc.
        explicit_match = re.search(f'{currency}(\\d+)([MY])', ticker_upper)
        if explicit_match:
            return f"{explicit_match.group(1)}{explicit_match.group(2)}"
        
        # Numeric patterns at the end
        end_num_match = re.search(r'(\d+)\s*(?:CURNCY|INDEX)?$', ticker_upper)
        if end_num_match:
            num = int(end_num_match.group(1))
            return f"{num}Y"  # Assume years for OIS
        
        return None
    
    def discover_all_currencies(self):
        """Main method to discover OIS tickers for all currencies"""
        logger.info("🚀 Starting efficient OIS ticker discovery")
        
        # Test Bloomberg connection first
        if not self.test_bloomberg_connection():
            logger.error("❌ Cannot proceed without Bloomberg API connection")
            return
        
        # Connect to database
        conn = self.connect_to_database()
        if not conn:
            logger.error("❌ Cannot proceed without database connection")
            return
        
        try:
            # Ensure table exists
            self.ensure_table_exists(conn)
            
            # Process G10 first (highest priority)
            all_currencies = ALL_CURRENCIES['G10'] + ALL_CURRENCIES['EM']
            
            for currency in all_currencies:
                logger.info(f"\n{'='*50}")
                logger.info(f"Processing {currency}")
                logger.info(f"{'='*50}")
                
                # Step 1: Discover tickers
                discovered = self.discover_currency_tickers(currency)
                if not discovered:
                    logger.warning(f"⚠️  No tickers discovered for {currency}")
                    continue
                
                # Step 2: Extract ticker codes for validation
                ticker_codes = [t.get('ticker', '') for t in discovered if t.get('ticker')]
                if not ticker_codes:
                    logger.warning(f"⚠️  No valid ticker codes found for {currency}")
                    continue
                
                # Step 3: Validate tickers using reference data
                validation_results = self.validate_tickers_with_reference_data(ticker_codes)
                if not validation_results:
                    logger.warning(f"⚠️  Validation failed for {currency}")
                    continue
                
                # Step 4: Store results
                self.discovered_tickers[currency] = discovered
                self.validated_tickers[currency] = validation_results
                
                # Step 5: Insert into database
                self.insert_validated_tickers(conn, currency, validation_results)
                
                # Rate limiting between currencies
                time.sleep(2)
            
            # Generate summary report
            self.generate_summary_report()
            
        finally:
            conn.close()
            logger.info("✅ Database connection closed")
    
    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_currencies_processed': len(self.discovered_tickers),
            'summary_by_currency': {},
            'tenor_coverage': {},
            'grand_totals': {
                'total_discovered': 0,
                'total_validated': 0,
                'total_valid': 0
            }
        }
        
        logger.info(f"\n{'='*60}")
        logger.info("EFFICIENT OIS DISCOVERY SUMMARY")
        logger.info(f"{'='*60}")
        
        for currency in self.discovered_tickers:
            discovered_count = len(self.discovered_tickers.get(currency, []))
            validated_results = self.validated_tickers.get(currency, {})
            valid_count = sum(1 for v in validated_results.values() if v)
            
            # Extract tenors from valid tickers
            valid_tickers = [ticker for ticker, valid in validated_results.items() if valid]
            tenors_found = []
            for ticker in valid_tickers:
                tenor = self.extract_tenor_from_ticker(ticker, currency)
                if tenor:
                    tenors_found.append(tenor)
            
            report['summary_by_currency'][currency] = {
                'discovered': discovered_count,
                'validated': len(validated_results),
                'valid': valid_count,
                'tenors_found': sorted(set(tenors_found)),
                'success_rate': f"{(valid_count/len(validated_results)*100):.1f}%" if validated_results else "0%"
            }
            
            report['tenor_coverage'][currency] = {
                'found': sorted(set(tenors_found)),
                'missing': [t for t in STANDARD_TENORS if t not in tenors_found]
            }
            
            report['grand_totals']['total_discovered'] += discovered_count
            report['grand_totals']['total_validated'] += len(validated_results)
            report['grand_totals']['total_valid'] += valid_count
            
            logger.info(f"{currency}: {valid_count} valid OIS tickers")
            logger.info(f"  Tenors: {', '.join(sorted(set(tenors_found)))}")
        
        # Save detailed report
        with open('efficient_ois_discovery_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        # Save detailed discovered tickers
        with open('efficient_ois_discovery_data.json', 'w') as f:
            json.dump({
                'discovered': self.discovered_tickers,
                'validated': self.validated_tickers
            }, f, indent=2)
        
        logger.info(f"\n📊 GRAND TOTALS:")
        logger.info(f"  Total discovered: {report['grand_totals']['total_discovered']}")
        logger.info(f"  Total validated: {report['grand_totals']['total_validated']}")
        logger.info(f"  Total valid: {report['grand_totals']['total_valid']}")
        
        overall_success = (report['grand_totals']['total_valid'] / 
                          max(report['grand_totals']['total_validated'], 1) * 100)
        logger.info(f"  Overall success rate: {overall_success:.1f}%")
        
        logger.info(f"\n📁 Reports saved:")
        logger.info(f"  - efficient_ois_discovery_report.json")
        logger.info(f"  - efficient_ois_discovery_data.json")
        logger.info(f"  - efficient_ois_discovery.log")

def main():
    """Main execution function"""
    discovery = EfficientOISDiscovery()
    discovery.discover_all_currencies()

if __name__ == "__main__":
    main()