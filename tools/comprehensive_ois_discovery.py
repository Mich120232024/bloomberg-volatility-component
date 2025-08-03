#!/usr/bin/env python3
"""
Comprehensive OIS Ticker Discovery and Database Population
Discovers and validates real OIS tickers for ALL currencies using Bloomberg API
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
        logging.FileHandler('ois_discovery.log'),
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
    # G10 currencies
    'G10': ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD', 'SEK', 'NOK'],
    # Emerging Market currencies
    'EM': ['MXN', 'ZAR', 'TRY', 'CNH', 'INR', 'KRW', 'TWD', 'SGD', 'HKD', 'THB', 
           'ILS', 'PLN', 'CZK', 'HUF', 'RUB', 'PHP', 'DKK', 'BRL']
}

class OISTickerDiscovery:
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
        """Discover OIS tickers for a specific currency with comprehensive search patterns"""
        logger.info(f"🔍 Discovering OIS tickers for {currency}")
        
        try:
            # Comprehensive search patterns for maximum coverage
            search_patterns = [
                # Direct OIS search
                {"search_type": "ois", "currency": currency, "max_results": 100},
                {"search_type": "swap", "currency": currency, "subcategory": "ois", "max_results": 100},
                
                # Generic patterns
                {"search_pattern": f"{currency} OIS", "max_results": 100},
                {"search_pattern": f"{currency} Overnight", "max_results": 100},
                {"search_pattern": f"{currency} Index Swap", "max_results": 100},
                
                # Common ticker patterns
                {"search_pattern": f"{currency}SO", "max_results": 100},  # USSO, EURSO etc
                {"search_pattern": f"{currency}OIS", "max_results": 100},
                {"search_pattern": f"{currency}OISD", "max_results": 100}, # Daily compounded
                {"search_pattern": f"{currency}SW", "max_results": 100},   # Generic swap
                
                # Specific tenor patterns
                {"search_pattern": f"{currency}SO1", "max_results": 50},   # 1Y OIS
                {"search_pattern": f"{currency}SO2", "max_results": 50},   # 2Y OIS
                {"search_pattern": f"{currency}SO5", "max_results": 50},   # 5Y OIS
                {"search_pattern": f"{currency}SO10", "max_results": 50},  # 10Y OIS
                
                # Alternative patterns for different markets
                {"search_pattern": f"{currency}ON", "max_results": 50},    # Overnight
                {"search_pattern": f"{currency}IBOR", "max_results": 50},  # Some markets use this
                {"search_pattern": f"{currency}IR", "max_results": 50},    # Interest Rate
                
                # Market-specific patterns
                {"search_pattern": f"{currency} SONIA" if currency == "GBP" else f"{currency} SOFR" if currency == "USD" else f"{currency} ESTR" if currency == "EUR" else f"{currency} TONAR" if currency == "JPY" else f"{currency} RFR", "max_results": 50},
            ]
            
            all_tickers = []
            
            for i, pattern in enumerate(search_patterns):
                try:
                    logger.info(f"  Trying pattern {i+1}/{len(search_patterns)}: {pattern}")
                    
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
                            logger.info(f"    ✅ Found {len(tickers)} tickers")
                            all_tickers.extend(tickers)
                        else:
                            logger.info(f"    ⚠️  No tickers found")
                    else:
                        logger.warning(f"    ❌ HTTP {response.status_code}")
                        
                    time.sleep(1.5)  # Rate limiting
                    
                except Exception as e:
                    logger.warning(f"    ❌ Pattern failed: {e}")
                    continue
            
            # Remove duplicates
            unique_tickers = []
            seen_tickers = set()
            for ticker in all_tickers:
                ticker_code = ticker.get('ticker', '')
                if ticker_code and ticker_code not in seen_tickers:
                    unique_tickers.append(ticker)
                    seen_tickers.add(ticker_code)
            
            logger.info(f"✅ Found {len(unique_tickers)} unique tickers for {currency}")
            
            # Filter for OIS-relevant tickers
            ois_tickers = []
            for ticker in unique_tickers:
                ticker_code = ticker.get('ticker', '')
                description = ticker.get('description', '').upper()
                
                # Check if it's OIS-related
                if self.is_ois_ticker(ticker_code, description, currency):
                    ois_tickers.append(ticker)
                    logger.info(f"    OIS: {ticker_code} - {description}")
            
            logger.info(f"✅ Filtered to {len(ois_tickers)} OIS-relevant tickers for {currency}")
            return ois_tickers
            
        except Exception as e:
            logger.error(f"❌ Error discovering {currency} tickers: {e}")
            return []
    
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
        
        if f'{currency}OIS' in ticker_upper:
            return True
            
        # Currency-specific patterns
        if currency == 'USD' and any(pattern in ticker_upper for pattern in ['SOFR', 'USSO']):
            return True
        elif currency == 'GBP' and any(pattern in ticker_upper for pattern in ['SONIA', 'GBPSO']):
            return True
        elif currency == 'EUR' and any(pattern in ticker_upper for pattern in ['ESTR', 'EURSO', 'EONIA']):
            return True
        elif currency == 'JPY' and any(pattern in ticker_upper for pattern in ['TONAR', 'JPYSO']):
            return True
        
        return False
    
    def validate_tickers(self, tickers: List[str]) -> Dict[str, bool]:
        """Validate tickers using Bloomberg API"""
        if not tickers:
            return {}
            
        logger.info(f"🔍 Validating {len(tickers)} tickers")
        
        try:
            # Validate in chunks of 20 to respect API limits
            chunk_size = 20
            validation_results = {}
            
            for i in range(0, len(tickers), chunk_size):
                chunk = tickers[i:i + chunk_size]
                
                response = requests.post(
                    f"{BLOOMBERG_API_URL}/api/bloomberg/validate-tickers",
                    headers=HEADERS,
                    json={
                        "tickers": chunk,
                        "fields": ["PX_LAST", "SECURITY_NAME", "SECURITY_DES"]
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        for validation in data.get("validations", []):
                            ticker = validation.get("ticker")
                            is_valid = validation.get("valid", False)
                            validation_results[ticker] = is_valid
                            
                            if is_valid:
                                logger.info(f"  ✅ {ticker} - Valid")
                            else:
                                error = validation.get("error", "Unknown error")
                                logger.warning(f"  ❌ {ticker} - Invalid: {error}")
                else:
                    logger.error(f"Validation API error: {response.status_code}")
                
                time.sleep(2)  # Rate limiting between chunks
            
            return validation_results
            
        except Exception as e:
            logger.error(f"❌ Error validating tickers: {e}")
            return {}
    
    def categorize_ois_tickers(self, tickers: List[Dict], currency: str) -> Dict[str, List[str]]:
        """Categorize tickers by tenor and type"""
        categorized = {
            'overnight': [],
            'short_term': [],  # 1W to 1M
            'medium_term': [], # 2M to 2Y
            'long_term': [],   # 3Y+
            'unknown': []
        }
        
        for ticker_info in tickers:
            ticker = ticker_info.get('ticker', '')
            description = ticker_info.get('description', '').upper()
            
            # Skip if not OIS-related
            if not any(term in description for term in ['OIS', 'OVERNIGHT', 'SWAP']):
                continue
            
            # Extract tenor information
            tenor = None
            if any(term in ticker for term in ['ON', 'O/N']):
                categorized['overnight'].append(ticker)
            elif any(f'{currency}SO{i}' in ticker for i in range(1, 13)):  # 1-12 months
                categorized['short_term'].append(ticker)
            elif any(f'{currency}SO{i}' in ticker for i in range(1, 3)):  # 1-2 years
                categorized['medium_term'].append(ticker)
            elif any(f'{currency}SO{i}' in ticker for i in range(3, 31)):  # 3-30 years
                categorized['long_term'].append(ticker)
            else:
                categorized['unknown'].append(ticker)
        
        return categorized
    
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
        """Extract tenor from ticker code with comprehensive patterns"""
        import re
        
        ticker_upper = ticker.upper()
        
        # Overnight patterns
        if any(pattern in ticker_upper for pattern in ['ON', 'O/N', 'OVERNIGHT']):
            return 'ON'
        
        # Week patterns
        week_match = re.search(r'(\d+)W', ticker_upper)
        if week_match:
            return f"{week_match.group(1)}W"
        
        # Common OIS patterns: USSO1, EURSO2, etc.
        ois_match = re.search(f'{currency}SO(\\d+)', ticker_upper)
        if ois_match:
            num = int(ois_match.group(1))
            if num <= 24:  # Up to 24 months
                return f"{num}M"
            else:
                return f"{num}Y"
        
        # Generic patterns with explicit M/Y: USD1Y, EUR6M, etc.
        explicit_match = re.search(f'{currency}(\\d+)([MY])', ticker_upper)
        if explicit_match:
            return f"{explicit_match.group(1)}{explicit_match.group(2)}"
        
        # Numeric patterns at the end: pattern like USOIS1, EUOIS5
        end_num_match = re.search(f'{currency}[A-Z]*?(\\d+)$', ticker_upper)
        if end_num_match:
            num = int(end_num_match.group(1))
            if num <= 24:
                return f"{num}M"
            else:
                return f"{num}Y"
        
        # Month patterns: 1M, 3M, 6M, etc.
        month_match = re.search(r'(\\d+)M', ticker_upper)
        if month_match:
            return f"{month_match.group(1)}M"
            
        # Year patterns: 1Y, 2Y, etc.
        year_match = re.search(r'(\\d+)Y', ticker_upper)
        if year_match:
            return f"{year_match.group(1)}Y"
        
        # Special cases for different market conventions
        special_tenors = {
            '1D': 'ON',
            '1W': '1W',
            '2W': '2W',
            '3W': '3W',
            '1M': '1M',
            '2M': '2M',
            '3M': '3M',
            '6M': '6M',
            '9M': '9M',
            '12M': '1Y',
            '18M': '18M',
            '24M': '2Y'
        }
        
        for pattern, tenor in special_tenors.items():
            if pattern in ticker_upper:
                return tenor
        
        return None
    
    def discover_all_currencies(self):
        """Main method to discover OIS tickers for all currencies"""
        logger.info("🚀 Starting comprehensive OIS ticker discovery")
        
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
                
                # Step 3: Validate tickers
                validation_results = self.validate_tickers(ticker_codes)
                if not validation_results:
                    logger.warning(f"⚠️  Validation failed for {currency}")
                    continue
                
                # Step 4: Store results
                self.discovered_tickers[currency] = discovered
                self.validated_tickers[currency] = validation_results
                
                # Step 5: Insert into database
                self.insert_validated_tickers(conn, currency, validation_results)
                
                # Rate limiting between currencies
                time.sleep(3)
            
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
            'grand_totals': {
                'total_discovered': 0,
                'total_validated': 0,
                'total_valid': 0
            }
        }
        
        logger.info(f"\n{'='*60}")
        logger.info("COMPREHENSIVE OIS DISCOVERY SUMMARY")
        logger.info(f"{'='*60}")
        
        for currency in self.discovered_tickers:
            discovered_count = len(self.discovered_tickers.get(currency, []))
            validated_results = self.validated_tickers.get(currency, {})
            valid_count = sum(1 for v in validated_results.values() if v)
            
            report['summary_by_currency'][currency] = {
                'discovered': discovered_count,
                'validated': len(validated_results),
                'valid': valid_count,
                'success_rate': f"{(valid_count/len(validated_results)*100):.1f}%" if validated_results else "0%"
            }
            
            report['grand_totals']['total_discovered'] += discovered_count
            report['grand_totals']['total_validated'] += len(validated_results)
            report['grand_totals']['total_valid'] += valid_count
            
            logger.info(f"{currency}: {discovered_count} discovered, {valid_count} valid")
        
        # Save detailed report
        with open('ois_discovery_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        # Save detailed discovered tickers
        with open('comprehensive_ois_discovery.json', 'w') as f:
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
        logger.info(f"  - ois_discovery_report.json")
        logger.info(f"  - comprehensive_ois_discovery.json")
        logger.info(f"  - ois_discovery.log")

def main():
    """Main execution function"""
    discovery = OISTickerDiscovery()
    discovery.discover_all_currencies()

if __name__ == "__main__":
    main()