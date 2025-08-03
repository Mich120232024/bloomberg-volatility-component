#!/usr/bin/env python3
"""
Final OIS Coverage Report Generator
Comprehensive analysis of all discovered OIS tickers and coverage
"""

import requests
import json
import psycopg2
import logging
from typing import Dict, List, Optional
from datetime import datetime
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database Configuration
DB_CONFIG = {
    'host': 'gzcdevserver.postgres.database.azure.com',
    'database': 'gzc_platform',
    'user': 'mikael',
    'password': 'Ii89rra137+*',
    'port': 5432,
    'sslmode': 'require'
}

# Standard tenor definitions
STANDARD_TENORS = ['ON', '1W', '2W', '3W', '1M', '2M', '3M', '6M', '9M', '1Y', '18M', '2Y', '3Y', '4Y', '5Y', '7Y', '10Y', '15Y', '20Y', '30Y']

# All currencies that were tested
ALL_TESTED_CURRENCIES = {
    'G10': ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD', 'SEK', 'NOK'],
    'EM': ['MXN', 'ZAR', 'TRY', 'CNH', 'INR', 'KRW', 'TWD', 'SGD', 'HKD', 'THB', 'ILS', 'PLN', 'CZK', 'HUF', 'RUB', 'PHP', 'DKK', 'BRL']
}

class OISCoverageAnalyzer:
    def __init__(self):
        self.db_tickers = {}
        self.tenor_analysis = {}
        self.pattern_analysis = {}
        
    def connect_to_database(self):
        """Connect to PostgreSQL database"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            logger.info("✅ Connected to PostgreSQL database")
            return conn
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            return None
    
    def extract_tenor_from_ticker(self, ticker: str) -> Optional[str]:
        """Extract tenor from ticker code"""
        ticker_upper = ticker.upper()
        
        # Overnight patterns
        if 'ON' in ticker_upper or 'O/N' in ticker_upper:
            return 'ON'
        
        # Week patterns
        week_match = re.search(r'(\d+)W', ticker_upper)
        if week_match:
            return f"{week_match.group(1)}W"
        
        # Month patterns
        month_match = re.search(r'(\d+)M', ticker_upper)
        if month_match:
            return f"{month_match.group(1)}M"
        
        # Year patterns - look for number followed by year indicators or at end
        year_patterns = [
            r'(\d+)Y',  # Explicit Y
            r'SO(\d+)',  # USSO1, EURSO2 etc.
            r'(\d+)\s*(?:CURNCY|INDEX|$)'  # Number at end
        ]
        
        for pattern in year_patterns:
            match = re.search(pattern, ticker_upper)
            if match:
                num = int(match.group(1))
                if num <= 24:  # Treat small numbers as months if no explicit Y
                    if 'Y' in pattern or 'SO' in pattern:
                        return f"{num}Y"
                    else:
                        return f"{num}M"
                else:
                    return f"{num}Y"
        
        return 'Unknown'
    
    def analyze_ticker_patterns(self, currency: str, tickers: List[str]) -> Dict:
        """Analyze ticker patterns for a currency"""
        patterns = {}
        
        for ticker in tickers:
            # Extract base pattern
            base_pattern = None
            if f'{currency}SO' in ticker:
                base_pattern = f'{currency}SO'
            elif f'{currency} ' in ticker:
                # For patterns like "EUR ESTR", "GBP SONIA"
                parts = ticker.split()
                if len(parts) >= 2:
                    base_pattern = f'{parts[0]} {parts[1]}'
            elif f'{currency}OIS' in ticker:
                base_pattern = f'{currency}OIS'
            else:
                # Try to extract other patterns
                for part in ticker.split():
                    if currency in part:
                        base_pattern = part.replace('CURNCY', '').replace('INDEX', '').strip()
                        break
            
            if base_pattern:
                patterns.setdefault(base_pattern, []).append(ticker)
            else:
                patterns.setdefault('Other', []).append(ticker)
        
        return patterns
    
    def load_database_tickers(self):
        """Load all OIS tickers from database"""
        conn = self.connect_to_database()
        if not conn:
            return
        
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT currency_code, bloomberg_ticker, curve_name
                    FROM ticker_reference 
                    WHERE instrument_type = 'OIS' AND is_active = true
                    ORDER BY currency_code, bloomberg_ticker
                """)
                
                results = cursor.fetchall()
                
                for currency, ticker, curve_name in results:
                    if currency not in self.db_tickers:
                        self.db_tickers[currency] = []
                    self.db_tickers[currency].append(ticker)
                
            conn.close()
            logger.info(f"✅ Loaded {sum(len(tickers) for tickers in self.db_tickers.values())} OIS tickers from database")
            
        except Exception as e:
            logger.error(f"❌ Failed to load database tickers: {e}")
    
    def analyze_tenor_coverage(self):
        """Analyze tenor coverage for each currency"""
        for currency, tickers in self.db_tickers.items():
            tenor_counts = {}
            tenor_tickers = {}
            
            for ticker in tickers:
                tenor = self.extract_tenor_from_ticker(ticker)
                tenor_counts[tenor] = tenor_counts.get(tenor, 0) + 1
                tenor_tickers.setdefault(tenor, []).append(ticker)
            
            # Analyze coverage
            covered_tenors = [t for t in STANDARD_TENORS if t in tenor_counts]
            missing_tenors = [t for t in STANDARD_TENORS if t not in tenor_counts]
            
            self.tenor_analysis[currency] = {
                'total_tickers': len(tickers),
                'tenor_counts': tenor_counts,
                'tenor_tickers': tenor_tickers,
                'covered_tenors': covered_tenors,
                'missing_tenors': missing_tenors,
                'coverage_pct': len(covered_tenors) / len(STANDARD_TENORS) * 100
            }
            
            # Analyze patterns
            self.pattern_analysis[currency] = self.analyze_ticker_patterns(currency, tickers)
    
    def generate_comprehensive_report(self):
        """Generate comprehensive coverage report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_currencies_tested': len(ALL_TESTED_CURRENCIES['G10']) + len(ALL_TESTED_CURRENCIES['EM']),
                'currencies_with_ois': len(self.db_tickers),
                'total_ois_tickers': sum(len(tickers) for tickers in self.db_tickers.values()),
                'g10_coverage': len([c for c in ALL_TESTED_CURRENCIES['G10'] if c in self.db_tickers]),
                'em_coverage': len([c for c in ALL_TESTED_CURRENCIES['EM'] if c in self.db_tickers])
            },
            'currencies_with_ois': {},
            'currencies_without_ois': {
                'G10': [c for c in ALL_TESTED_CURRENCIES['G10'] if c not in self.db_tickers],
                'EM': [c for c in ALL_TESTED_CURRENCIES['EM'] if c not in self.db_tickers]
            },
            'detailed_analysis': {},
            'tenor_coverage_summary': {},
            'pattern_summary': {}
        }
        
        # Detailed analysis per currency
        for currency in self.db_tickers:
            tickers = self.db_tickers[currency]
            tenor_info = self.tenor_analysis[currency]
            pattern_info = self.pattern_analysis[currency]
            
            report['currencies_with_ois'][currency] = {
                'ticker_count': len(tickers),
                'tenor_coverage_pct': tenor_info['coverage_pct'],
                'covered_tenors': tenor_info['covered_tenors'],
                'missing_tenors': tenor_info['missing_tenors'],
                'main_patterns': list(pattern_info.keys()),
                'sample_tickers': tickers[:5]  # First 5 as examples
            }
            
            report['detailed_analysis'][currency] = {
                'tenor_analysis': tenor_info,
                'pattern_analysis': pattern_info
            }
        
        # Tenor coverage summary across all currencies
        tenor_coverage = {}
        for tenor in STANDARD_TENORS:
            currencies_with_tenor = [c for c in self.db_tickers if tenor in self.tenor_analysis[c]['covered_tenors']]
            tenor_coverage[tenor] = {
                'currencies_count': len(currencies_with_tenor),
                'currencies': currencies_with_tenor,
                'coverage_pct': len(currencies_with_tenor) / len(self.db_tickers) * 100 if self.db_tickers else 0
            }
        
        report['tenor_coverage_summary'] = tenor_coverage
        
        # Pattern summary
        all_patterns = set()
        for currency_patterns in self.pattern_analysis.values():
            all_patterns.update(currency_patterns.keys())
        
        pattern_summary = {}
        for pattern in all_patterns:
            currencies_with_pattern = [c for c in self.db_tickers if pattern in self.pattern_analysis[c]]
            pattern_summary[pattern] = {
                'currencies_count': len(currencies_with_pattern),
                'currencies': currencies_with_pattern
            }
        
        report['pattern_summary'] = pattern_summary
        
        return report
    
    def print_report_summary(self, report: Dict):
        """Print human-readable summary"""
        logger.info(f"\n{'='*80}")
        logger.info("COMPREHENSIVE OIS TICKER DISCOVERY - FINAL REPORT")
        logger.info(f"{'='*80}")
        
        summary = report['summary']
        logger.info(f"📊 OVERALL SUMMARY:")
        logger.info(f"  Total currencies tested: {summary['total_currencies_tested']}")
        logger.info(f"  Currencies with OIS: {summary['currencies_with_ois']}")
        logger.info(f"  Total OIS tickers found: {summary['total_ois_tickers']}")
        logger.info(f"  G10 coverage: {summary['g10_coverage']}/10 ({summary['g10_coverage']/10*100:.0f}%)")
        logger.info(f"  EM coverage: {summary['em_coverage']}/18 ({summary['em_coverage']/18*100:.0f}%)")
        
        logger.info(f"\n✅ CURRENCIES WITH OIS TICKERS:")
        for currency, info in report['currencies_with_ois'].items():
            logger.info(f"  {currency}: {info['ticker_count']} tickers, {info['tenor_coverage_pct']:.0f}% tenor coverage")
            logger.info(f"    Patterns: {', '.join(info['main_patterns'])}")
            logger.info(f"    Sample: {', '.join(info['sample_tickers'][:3])}")
        
        logger.info(f"\n❌ CURRENCIES WITHOUT OIS TICKERS:")
        if report['currencies_without_ois']['G10']:
            logger.info(f"  G10: {', '.join(report['currencies_without_ois']['G10'])}")
        if report['currencies_without_ois']['EM']:
            logger.info(f"  EM: {', '.join(report['currencies_without_ois']['EM'])}")
        
        logger.info(f"\n📈 TENOR COVERAGE ANALYSIS:")
        tenor_summary = report['tenor_coverage_summary']
        for tenor in ['ON', '1W', '1M', '3M', '6M', '1Y', '2Y', '5Y', '10Y', '30Y']:  # Key tenors
            if tenor in tenor_summary:
                info = tenor_summary[tenor]
                logger.info(f"  {tenor}: {info['currencies_count']}/{len(self.db_tickers)} currencies ({info['coverage_pct']:.0f}%)")
        
        logger.info(f"\n🔧 PATTERN ANALYSIS:")
        pattern_summary = report['pattern_summary']
        for pattern, info in sorted(pattern_summary.items(), key=lambda x: x[1]['currencies_count'], reverse=True):
            if info['currencies_count'] > 1:  # Show patterns used by multiple currencies
                logger.info(f"  {pattern}: {info['currencies_count']} currencies ({', '.join(info['currencies'])})")
    
    def analyze_and_report(self):
        """Main analysis and reporting function"""
        logger.info("🚀 Starting comprehensive OIS coverage analysis")
        
        # Load data
        self.load_database_tickers()
        if not self.db_tickers:
            logger.error("❌ No OIS tickers found in database")
            return
        
        # Analyze
        self.analyze_tenor_coverage()
        
        # Generate report
        report = self.generate_comprehensive_report()
        
        # Print summary
        self.print_report_summary(report)
        
        # Save detailed report
        with open('comprehensive_ois_coverage_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        # Save simplified summary
        simplified_summary = {
            'timestamp': report['timestamp'],
            'summary': report['summary'],
            'currencies_with_ois': {
                currency: {
                    'ticker_count': info['ticker_count'],
                    'tenor_coverage_pct': info['tenor_coverage_pct'],
                    'main_patterns': info['main_patterns']
                }
                for currency, info in report['currencies_with_ois'].items()
            },
            'currencies_without_ois': report['currencies_without_ois']
        }
        
        with open('ois_discovery_summary.json', 'w') as f:
            json.dump(simplified_summary, f, indent=2)
        
        logger.info(f"\n📁 REPORTS SAVED:")
        logger.info(f"  - comprehensive_ois_coverage_report.json (detailed)")
        logger.info(f"  - ois_discovery_summary.json (simplified)")
        
        logger.info(f"\n💾 DATABASE STATUS:")
        logger.info(f"  Table: ticker_reference")
        logger.info(f"  OIS records: {report['summary']['total_ois_tickers']}")
        logger.info(f"  Currencies covered: {report['summary']['currencies_with_ois']}")

def main():
    """Main execution function"""
    analyzer = OISCoverageAnalyzer()
    analyzer.analyze_and_report()

if __name__ == "__main__":
    main()