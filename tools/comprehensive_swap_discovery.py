#!/usr/bin/env python3
"""
Comprehensive Bloomberg Swap Discovery and Database Population
============================================================

This script systematically discovers ALL Bloomberg swap instruments across:
1. Interest Rate Swaps (IRS) 
2. Overnight Index Swaps (OIS)
3. Basis Swaps
4. Swap Indices

For ALL G10 + EM currencies and populates the complete database.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
import httpx
import psycopg2
from psycopg2.extras import RealDictCursor
import argparse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('comprehensive_swap_discovery.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class SwapDiscoveryConfig:
    """Configuration for swap discovery"""
    bloomberg_api_url: str = "http://20.172.249.92:8080"
    max_results_per_search: int = 100
    validation_batch_size: int = 50
    rate_limit_delay: float = 0.5  # seconds between API calls
    
    # Database configuration
    db_host: str = "gzcdevserver.postgres.database.azure.com"
    db_name: str = "gzc_platform"
    db_user: str = "gzcdev"
    db_password: str = "gzc-admin-2025!"
    db_port: int = 5432

@dataclass
class SwapInstrument:
    """Represents a discovered swap instrument"""
    ticker: str
    description: str
    currency: str
    tenor: str
    tenor_days: int
    swap_type: str  # 'irs', 'ois', 'basis_swap', 'swap_index'
    properties: Dict
    is_validated: bool = False

class SwapDiscoveryEngine:
    """Main engine for discovering and validating swap instruments"""
    
    def __init__(self, config: SwapDiscoveryConfig):
        self.config = config
        self.session = httpx.AsyncClient(timeout=30.0)
        self.discovered_instruments: List[SwapInstrument] = []
        self.validation_cache: Set[str] = set()
        
        # Define search configurations
        self.swap_types = {
            'irs': 'Interest Rate Swaps',
            'ois': 'Overnight Index Swaps', 
            'basis_swaps': 'Basis Swaps',
            'swap_indices': 'Swap Indices'
        }
        
        self.currencies = {
            # G10 currencies
            'USD': 'US Dollar',
            'EUR': 'Euro',
            'GBP': 'British Pound',
            'JPY': 'Japanese Yen',
            'CHF': 'Swiss Franc',
            'CAD': 'Canadian Dollar',
            'AUD': 'Australian Dollar',
            'NZD': 'New Zealand Dollar',
            'SEK': 'Swedish Krona',
            'NOK': 'Norwegian Krone',
            
            # Emerging Market currencies
            'MXN': 'Mexican Peso',
            'ZAR': 'South African Rand',
            'TRY': 'Turkish Lira',
            'CNH': 'Chinese Yuan (Offshore)',
            'INR': 'Indian Rupee',
            'KRW': 'Korean Won',
            'TWD': 'Taiwan Dollar',
            'SGD': 'Singapore Dollar',
            'HKD': 'Hong Kong Dollar',
            'THB': 'Thai Baht',
            'ILS': 'Israeli Shekel',
            'PLN': 'Polish Zloty',
            'CZK': 'Czech Koruna',
            'HUF': 'Hungarian Forint',
            'RUB': 'Russian Ruble',
            'PHP': 'Philippine Peso',
            'DKK': 'Danish Krone',
            'BRL': 'Brazilian Real'
        }
        
        # Standard swap tenors for comprehensive coverage
        self.standard_tenors = [
            '1M', '2M', '3M', '6M', '9M', '1Y', '18M', '2Y', '3Y', '4Y', '5Y',
            '6Y', '7Y', '8Y', '9Y', '10Y', '12Y', '15Y', '20Y', '25Y', '30Y'
        ]

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.aclose()

    def get_db_connection(self):
        """Create database connection"""
        return psycopg2.connect(
            host=self.config.db_host,
            database=self.config.db_name,
            user=self.config.db_user,
            password=self.config.db_password,
            port=self.config.db_port
        )

    async def discover_swaps_for_type_currency(
        self, 
        swap_type: str, 
        currency: str
    ) -> List[SwapInstrument]:
        """Discover swaps for a specific type and currency"""
        
        logger.info(f"Discovering {swap_type} swaps for {currency}")
        
        headers = {
            "Authorization": "Bearer test",
            "Content-Type": "application/json"
        }
        
        payload = {
            "search_type": swap_type,
            "currency": currency,
            "max_results": self.config.max_results_per_search
        }
        
        try:
            await asyncio.sleep(self.config.rate_limit_delay)
            
            response = await self.session.post(
                f"{self.config.bloomberg_api_url}/api/bloomberg/ticker-discovery",
                json=payload,
                headers=headers
            )
            
            if response.status_code != 200:
                logger.error(f"Discovery failed for {swap_type}/{currency}: {response.status_code}")
                return []
            
            data = response.json()
            discovered = []
            
            if 'tickers' in data and data['tickers']:
                for ticker_info in data['tickers']:
                    if isinstance(ticker_info, dict):
                        ticker = ticker_info.get('ticker', '')
                        description = ticker_info.get('description', '')
                        tenor = ticker_info.get('tenor', '')
                        tenor_days = ticker_info.get('tenor_days', 0)
                    else:
                        ticker = str(ticker_info)
                        description = ''
                        tenor = ''
                        tenor_days = 0
                    
                    if ticker:
                        instrument = SwapInstrument(
                            ticker=ticker,
                            description=description,
                            currency=currency,
                            tenor=tenor,
                            tenor_days=tenor_days,
                            swap_type=swap_type,
                            properties={
                                'search_type': swap_type,
                                'discovery_method': 'bloomberg_api'
                            }
                        )
                        discovered.append(instrument)
            
            logger.info(f"Discovered {len(discovered)} {swap_type} instruments for {currency}")
            return discovered
            
        except Exception as e:
            logger.error(f"Error discovering {swap_type} for {currency}: {e}")
            return []

    async def validate_tickers_batch(self, tickers: List[str]) -> Dict[str, bool]:
        """Validate a batch of Bloomberg tickers"""
        
        if not tickers:
            return {}
        
        headers = {
            "Authorization": "Bearer test",
            "Content-Type": "application/json"
        }
        
        try:
            await asyncio.sleep(self.config.rate_limit_delay)
            
            response = await self.session.post(
                f"{self.config.bloomberg_api_url}/api/bloomberg/validate-tickers",
                json=tickers,
                headers=headers
            )
            
            if response.status_code != 200:
                logger.error(f"Validation failed: {response.status_code}")
                return {ticker: False for ticker in tickers}
            
            data = response.json()
            
            # Handle different response formats
            if isinstance(data, dict) and 'results' in data:
                return data['results']
            elif isinstance(data, dict):
                return data
            else:
                return {ticker: False for ticker in tickers}
                
        except Exception as e:
            logger.error(f"Error validating tickers: {e}")
            return {ticker: False for ticker in tickers}

    async def discover_all_swaps(self) -> List[SwapInstrument]:
        """Discover all swap instruments across all types and currencies"""
        
        logger.info("Starting comprehensive swap discovery...")
        all_instruments = []
        
        total_combinations = len(self.swap_types) * len(self.currencies)
        completed = 0
        
        for swap_type in self.swap_types.keys():
            for currency in self.currencies.keys():
                logger.info(f"Progress: {completed}/{total_combinations} - Discovering {swap_type} for {currency}")
                
                instruments = await self.discover_swaps_for_type_currency(swap_type, currency)
                all_instruments.extend(instruments)
                
                completed += 1
                
                # Rate limiting
                await asyncio.sleep(self.config.rate_limit_delay)
        
        logger.info(f"Discovery complete. Found {len(all_instruments)} total instruments")
        return all_instruments

    async def validate_all_instruments(self, instruments: List[SwapInstrument]) -> List[SwapInstrument]:
        """Validate all discovered instruments"""
        
        logger.info(f"Validating {len(instruments)} discovered instruments...")
        
        # Group by unique tickers to avoid duplicate validation
        unique_tickers = list(set(instr.ticker for instr in instruments))
        logger.info(f"Validating {len(unique_tickers)} unique tickers")
        
        validation_results = {}
        
        # Process in batches
        for i in range(0, len(unique_tickers), self.config.validation_batch_size):
            batch = unique_tickers[i:i + self.config.validation_batch_size]
            logger.info(f"Validating batch {i//self.config.validation_batch_size + 1}: {len(batch)} tickers")
            
            batch_results = await self.validate_tickers_batch(batch)
            validation_results.update(batch_results)
            
            # Rate limiting between batches
            await asyncio.sleep(self.config.rate_limit_delay * 2)
        
        # Apply validation results
        validated_instruments = []
        for instrument in instruments:
            instrument.is_validated = validation_results.get(instrument.ticker, False)
            if instrument.is_validated:
                validated_instruments.append(instrument)
        
        logger.info(f"Validation complete. {len(validated_instruments)} valid instruments out of {len(instruments)}")
        return validated_instruments

    def populate_database(self, instruments: List[SwapInstrument]) -> None:
        """Populate database with discovered and validated instruments"""
        
        logger.info(f"Populating database with {len(instruments)} validated instruments...")
        
        with self.get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                
                # 1. Populate ticker_reference table
                logger.info("Populating ticker_reference table...")
                ticker_insert_count = 0
                
                for instrument in instruments:
                    try:
                        cur.execute("""
                            INSERT INTO ticker_reference (
                                ticker, description, asset_class, currency, 
                                instrument_type, properties, tenor_years
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (ticker) DO UPDATE SET
                                description = EXCLUDED.description,
                                properties = EXCLUDED.properties,
                                last_updated = CURRENT_TIMESTAMP
                        """, (
                            instrument.ticker,
                            instrument.description,
                            'rates',
                            instrument.currency,
                            instrument.swap_type,
                            json.dumps(instrument.properties),
                            instrument.tenor_days / 365.25 if instrument.tenor_days > 0 else None
                        ))
                        ticker_insert_count += 1
                    except Exception as e:
                        logger.error(f"Error inserting ticker {instrument.ticker}: {e}")
                
                logger.info(f"Inserted/updated {ticker_insert_count} tickers in ticker_reference")
                
                # 2. Populate bloomberg_tickers table
                logger.info("Populating bloomberg_tickers table...")
                bloomberg_insert_count = 0
                
                for instrument in instruments:
                    try:
                        cur.execute("""
                            INSERT INTO bloomberg_tickers (
                                bloomberg_ticker, description, currency, tenor,
                                tenor_numeric, category, subcategory, properties,
                                validation_status, last_validated_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (bloomberg_ticker) DO UPDATE SET
                                description = EXCLUDED.description,
                                properties = EXCLUDED.properties,
                                validation_status = EXCLUDED.validation_status,
                                last_validated_at = EXCLUDED.last_validated_at
                        """, (
                            instrument.ticker,
                            instrument.description,
                            instrument.currency,
                            instrument.tenor,
                            instrument.tenor_days,
                            'swap',
                            instrument.swap_type,
                            json.dumps(instrument.properties),
                            'valid' if instrument.is_validated else 'invalid',
                            datetime.now()
                        ))
                        bloomberg_insert_count += 1
                    except Exception as e:
                        logger.error(f"Error inserting Bloomberg ticker {instrument.ticker}: {e}")
                
                logger.info(f"Inserted/updated {bloomberg_insert_count} tickers in bloomberg_tickers")
                
                # 3. Create rate curve definitions
                logger.info("Creating rate curve definitions...")
                curve_definitions = self.generate_curve_definitions(instruments)
                curve_insert_count = 0
                
                for curve_def in curve_definitions:
                    try:
                        cur.execute("""
                            INSERT INTO rate_curve_definitions (
                                curve_name, currency_code, curve_type, methodology
                            ) VALUES (%s, %s, %s, %s)
                            ON CONFLICT (curve_name) DO UPDATE SET
                                methodology = EXCLUDED.methodology,
                                updated_at = CURRENT_TIMESTAMP
                        """, (
                            curve_def['curve_name'],
                            curve_def['currency_code'],
                            curve_def['curve_type'],
                            curve_def['methodology']
                        ))
                        curve_insert_count += 1
                    except Exception as e:
                        logger.error(f"Error inserting curve definition {curve_def['curve_name']}: {e}")
                
                logger.info(f"Inserted/updated {curve_insert_count} curve definitions")
                
                # 4. Create rate curve mappings
                logger.info("Creating rate curve mappings...")
                mappings = self.generate_curve_mappings(instruments)
                mapping_insert_count = 0
                
                for mapping in mappings:
                    try:
                        cur.execute("""
                            INSERT INTO rate_curve_mappings (
                                curve_name, bloomberg_ticker, sorting_order
                            ) VALUES (%s, %s, %s)
                            ON CONFLICT (curve_name, bloomberg_ticker) DO UPDATE SET
                                sorting_order = EXCLUDED.sorting_order
                        """, (
                            mapping['curve_name'],
                            mapping['bloomberg_ticker'],
                            mapping['sorting_order']
                        ))
                        mapping_insert_count += 1
                    except Exception as e:
                        logger.error(f"Error inserting mapping {mapping['curve_name']}/{mapping['bloomberg_ticker']}: {e}")
                
                logger.info(f"Inserted/updated {mapping_insert_count} curve mappings")
                
                conn.commit()
                logger.info("Database population completed successfully")

    def generate_curve_definitions(self, instruments: List[SwapInstrument]) -> List[Dict]:
        """Generate curve definitions from discovered instruments"""
        
        curve_defs = []
        
        # Group instruments by currency and swap type
        groups = {}
        for instrument in instruments:
            key = (instrument.currency, instrument.swap_type)
            if key not in groups:
                groups[key] = []
            groups[key].append(instrument)
        
        for (currency, swap_type), instr_list in groups.items():
            
            # Map swap types to curve types
            curve_type_mapping = {
                'irs': 'IRS',
                'ois': 'OIS', 
                'basis_swaps': 'BASIS',
                'swap_indices': 'INDEX'
            }
            
            curve_type = curve_type_mapping.get(swap_type, swap_type.upper())
            curve_name = f"{currency}_{curve_type}"
            
            methodology = f"Bloomberg {self.swap_types[swap_type]} for {currency} - " \
                         f"constructed from {len(instr_list)} instruments"
            
            curve_defs.append({
                'curve_name': curve_name,
                'currency_code': currency,
                'curve_type': curve_type,
                'methodology': methodology
            })
        
        return curve_defs

    def generate_curve_mappings(self, instruments: List[SwapInstrument]) -> List[Dict]:
        """Generate curve mappings from discovered instruments"""
        
        mappings = []
        
        # Group instruments by currency and swap type
        groups = {}
        for instrument in instruments:
            key = (instrument.currency, instrument.swap_type)
            if key not in groups:
                groups[key] = []
            groups[key].append(instrument)
        
        for (currency, swap_type), instr_list in groups.items():
            
            curve_type_mapping = {
                'irs': 'IRS',
                'ois': 'OIS',
                'basis_swaps': 'BASIS', 
                'swap_indices': 'INDEX'
            }
            
            curve_type = curve_type_mapping.get(swap_type, swap_type.upper())
            curve_name = f"{currency}_{curve_type}"
            
            # Sort instruments by tenor for proper ordering
            sorted_instruments = sorted(instr_list, key=lambda x: x.tenor_days)
            
            for i, instrument in enumerate(sorted_instruments):
                mappings.append({
                    'curve_name': curve_name,
                    'bloomberg_ticker': instrument.ticker,
                    'sorting_order': i + 1
                })
        
        return mappings

    def generate_discovery_report(self, instruments: List[SwapInstrument]) -> Dict:
        """Generate comprehensive discovery report"""
        
        report = {
            'discovery_timestamp': datetime.now().isoformat(),
            'total_instruments': len(instruments),
            'validated_instruments': len([i for i in instruments if i.is_validated]),
            'by_swap_type': {},
            'by_currency': {},
            'by_currency_type': {},
            'coverage_gaps': []
        }
        
        # Group by swap type
        for swap_type in self.swap_types.keys():
            type_instruments = [i for i in instruments if i.swap_type == swap_type]
            report['by_swap_type'][swap_type] = {
                'total': len(type_instruments),
                'validated': len([i for i in type_instruments if i.is_validated]),
                'currencies': list(set(i.currency for i in type_instruments))
            }
        
        # Group by currency
        for currency in self.currencies.keys():
            curr_instruments = [i for i in instruments if i.currency == currency]
            report['by_currency'][currency] = {
                'total': len(curr_instruments),
                'validated': len([i for i in curr_instruments if i.is_validated]),
                'swap_types': list(set(i.swap_type for i in curr_instruments))
            }
        
        # Group by currency + type combination
        for currency in self.currencies.keys():
            for swap_type in self.swap_types.keys():
                key = f"{currency}_{swap_type}"
                combo_instruments = [
                    i for i in instruments 
                    if i.currency == currency and i.swap_type == swap_type
                ]
                if combo_instruments:
                    report['by_currency_type'][key] = {
                        'total': len(combo_instruments),
                        'validated': len([i for i in combo_instruments if i.is_validated]),
                        'tenors': sorted(list(set(i.tenor for i in combo_instruments if i.tenor)))
                    }
        
        # Identify coverage gaps
        for currency in self.currencies.keys():
            for swap_type in self.swap_types.keys():
                combo_instruments = [
                    i for i in instruments 
                    if i.currency == currency and i.swap_type == swap_type and i.is_validated
                ]
                if not combo_instruments:
                    report['coverage_gaps'].append(f"{currency}_{swap_type}")
        
        return report

async def main():
    """Main execution function"""
    
    parser = argparse.ArgumentParser(description="Comprehensive Bloomberg Swap Discovery")
    parser.add_argument("--dry-run", action="store_true", help="Discovery only, no database updates")
    parser.add_argument("--currencies", nargs="+", help="Specific currencies to discover (default: all)")
    parser.add_argument("--swap-types", nargs="+", help="Specific swap types to discover (default: all)")
    parser.add_argument("--output-file", default="comprehensive_swap_discovery_results.json", 
                       help="Output file for discovery results")
    
    args = parser.parse_args()
    
    config = SwapDiscoveryConfig()
    
    async with SwapDiscoveryEngine(config) as engine:
        
        # Override currencies/swap types if specified
        if args.currencies:
            engine.currencies = {c: engine.currencies.get(c, c) for c in args.currencies if c in engine.currencies}
        if args.swap_types:
            engine.swap_types = {s: engine.swap_types.get(s, s) for s in args.swap_types if s in engine.swap_types}
        
        logger.info(f"Discovering swaps for {len(engine.currencies)} currencies and {len(engine.swap_types)} swap types")
        
        # Step 1: Discovery
        start_time = time.time()
        all_instruments = await engine.discover_all_swaps()
        discovery_time = time.time() - start_time
        
        logger.info(f"Discovery completed in {discovery_time:.2f} seconds")
        
        # Step 2: Validation
        start_time = time.time()
        validated_instruments = await engine.validate_all_instruments(all_instruments)
        validation_time = time.time() - start_time
        
        logger.info(f"Validation completed in {validation_time:.2f} seconds")
        
        # Step 3: Generate report
        report = engine.generate_discovery_report(validated_instruments)
        
        # Save results
        results = {
            'config': {
                'currencies': list(engine.currencies.keys()),
                'swap_types': list(engine.swap_types.keys()),
                'discovery_time_seconds': discovery_time,
                'validation_time_seconds': validation_time
            },
            'instruments': [
                {
                    'ticker': i.ticker,
                    'description': i.description,
                    'currency': i.currency,
                    'tenor': i.tenor,
                    'tenor_days': i.tenor_days,
                    'swap_type': i.swap_type,
                    'is_validated': i.is_validated,
                    'properties': i.properties
                } for i in validated_instruments
            ],
            'report': report
        }
        
        with open(args.output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved to {args.output_file}")
        
        # Step 4: Database population (unless dry run)
        if not args.dry_run:
            start_time = time.time()
            engine.populate_database(validated_instruments)
            db_time = time.time() - start_time
            logger.info(f"Database population completed in {db_time:.2f} seconds")
        else:
            logger.info("Dry run mode - skipping database population")
        
        # Final summary
        logger.info("=" * 80)
        logger.info("COMPREHENSIVE SWAP DISCOVERY COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total instruments discovered: {len(all_instruments)}")
        logger.info(f"Valid instruments: {len(validated_instruments)}")
        logger.info(f"Validation rate: {len(validated_instruments)/len(all_instruments)*100:.1f}%")
        logger.info(f"Currencies covered: {len(report['by_currency'])}")
        logger.info(f"Swap types covered: {len(report['by_swap_type'])}")
        logger.info(f"Coverage gaps: {len(report['coverage_gaps'])}")
        
        if report['coverage_gaps']:
            logger.info("Coverage gaps found for:")
            for gap in report['coverage_gaps']:
                logger.info(f"  - {gap}")

if __name__ == "__main__":
    asyncio.run(main())