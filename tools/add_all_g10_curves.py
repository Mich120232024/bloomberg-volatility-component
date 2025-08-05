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

# G10 curves configuration
g10_configs = {
    'JPY': {
        'curve_name': 'JPY_OIS',
        'curve_type': 'OIS',
        'methodology': 'Tokyo Overnight Average Rate (TONAR) based overnight indexed swap curve',
        'primary_use': 'Risk-free rate benchmark',
        'tickers': [
            {'ticker': 'MUTKCALM Index', 'tenor': 'O/N', 'tenor_numeric': 1, 'category': 'RATE'},
            {'ticker': 'JYSOA Curncy', 'tenor': '1M', 'tenor_numeric': 30, 'category': 'SWAP'},
            {'ticker': 'JYSOB Curncy', 'tenor': '2M', 'tenor_numeric': 60, 'category': 'SWAP'},
            {'ticker': 'JYSOC Curncy', 'tenor': '3M', 'tenor_numeric': 90, 'category': 'SWAP'},
            {'ticker': 'JYSOD Curncy', 'tenor': '4M', 'tenor_numeric': 120, 'category': 'SWAP'},
            {'ticker': 'JYSOE Curncy', 'tenor': '5M', 'tenor_numeric': 150, 'category': 'SWAP'},
            {'ticker': 'JYSOF Curncy', 'tenor': '6M', 'tenor_numeric': 180, 'category': 'SWAP'},
            {'ticker': 'JYSOG Curncy', 'tenor': '7M', 'tenor_numeric': 210, 'category': 'SWAP'},
            {'ticker': 'JYSOH Curncy', 'tenor': '8M', 'tenor_numeric': 240, 'category': 'SWAP'},
            {'ticker': 'JYSOI Curncy', 'tenor': '9M', 'tenor_numeric': 270, 'category': 'SWAP'},
            {'ticker': 'JYSOJ Curncy', 'tenor': '10M', 'tenor_numeric': 300, 'category': 'SWAP'},
            {'ticker': 'JYSOK Curncy', 'tenor': '11M', 'tenor_numeric': 330, 'category': 'SWAP'},
            {'ticker': 'JYSO1 Curncy', 'tenor': '1Y', 'tenor_numeric': 1, 'category': 'SWAP'},
            {'ticker': 'JYSO2 Curncy', 'tenor': '2Y', 'tenor_numeric': 2, 'category': 'SWAP'},
            {'ticker': 'JYSO3 Curncy', 'tenor': '3Y', 'tenor_numeric': 3, 'category': 'SWAP'},
            {'ticker': 'JYSO4 Curncy', 'tenor': '4Y', 'tenor_numeric': 4, 'category': 'SWAP'},
            {'ticker': 'JYSO5 Curncy', 'tenor': '5Y', 'tenor_numeric': 5, 'category': 'SWAP'},
            {'ticker': 'JYSO7 Curncy', 'tenor': '7Y', 'tenor_numeric': 7, 'category': 'SWAP'},
            {'ticker': 'JYSO10 Curncy', 'tenor': '10Y', 'tenor_numeric': 10, 'category': 'SWAP'},
            {'ticker': 'JYSO15 Curncy', 'tenor': '15Y', 'tenor_numeric': 15, 'category': 'SWAP'},
            {'ticker': 'JYSO20 Curncy', 'tenor': '20Y', 'tenor_numeric': 20, 'category': 'SWAP'},
            {'ticker': 'JYSO30 Curncy', 'tenor': '30Y', 'tenor_numeric': 30, 'category': 'SWAP'},
        ]
    },
    'CHF': {
        'curve_name': 'CHF_OIS',
        'curve_type': 'OIS',
        'methodology': 'Swiss Average Rate Overnight (SARON) based overnight indexed swap curve',
        'primary_use': 'Risk-free rate benchmark',
        'tickers': [
            {'ticker': 'SSARON Index', 'tenor': 'O/N', 'tenor_numeric': 1, 'category': 'RATE'},
            # CHF doesn't have standard OIS swaps, would need IRS tickers
        ]
    },
    'CAD': {
        'curve_name': 'CAD_OIS',
        'curve_type': 'OIS',
        'methodology': 'Canadian Overnight Repo Rate Average (CORRA) based overnight indexed swap curve',
        'primary_use': 'Risk-free rate benchmark',
        'tickers': [
            {'ticker': 'CAONREPO Index', 'tenor': 'O/N', 'tenor_numeric': 1, 'category': 'RATE'},
            {'ticker': 'CDSOA Curncy', 'tenor': '1M', 'tenor_numeric': 30, 'category': 'SWAP'},
            {'ticker': 'CDSOB Curncy', 'tenor': '2M', 'tenor_numeric': 60, 'category': 'SWAP'},
            {'ticker': 'CDSOC Curncy', 'tenor': '3M', 'tenor_numeric': 90, 'category': 'SWAP'},
            {'ticker': 'CDSOD Curncy', 'tenor': '4M', 'tenor_numeric': 120, 'category': 'SWAP'},
            {'ticker': 'CDSOE Curncy', 'tenor': '5M', 'tenor_numeric': 150, 'category': 'SWAP'},
            {'ticker': 'CDSOF Curncy', 'tenor': '6M', 'tenor_numeric': 180, 'category': 'SWAP'},
            {'ticker': 'CDSOG Curncy', 'tenor': '7M', 'tenor_numeric': 210, 'category': 'SWAP'},
            {'ticker': 'CDSOH Curncy', 'tenor': '8M', 'tenor_numeric': 240, 'category': 'SWAP'},
            {'ticker': 'CDSOI Curncy', 'tenor': '9M', 'tenor_numeric': 270, 'category': 'SWAP'},
            {'ticker': 'CDSOJ Curncy', 'tenor': '10M', 'tenor_numeric': 300, 'category': 'SWAP'},
            {'ticker': 'CDSOK Curncy', 'tenor': '11M', 'tenor_numeric': 330, 'category': 'SWAP'},
            {'ticker': 'CDSO1 Curncy', 'tenor': '1Y', 'tenor_numeric': 1, 'category': 'SWAP'},
            {'ticker': 'CDSO2 Curncy', 'tenor': '2Y', 'tenor_numeric': 2, 'category': 'SWAP'},
            {'ticker': 'CDSO3 Curncy', 'tenor': '3Y', 'tenor_numeric': 3, 'category': 'SWAP'},
            {'ticker': 'CDSO4 Curncy', 'tenor': '4Y', 'tenor_numeric': 4, 'category': 'SWAP'},
            {'ticker': 'CDSO5 Curncy', 'tenor': '5Y', 'tenor_numeric': 5, 'category': 'SWAP'},
            {'ticker': 'CDSO7 Curncy', 'tenor': '7Y', 'tenor_numeric': 7, 'category': 'SWAP'},
            {'ticker': 'CDSO10 Curncy', 'tenor': '10Y', 'tenor_numeric': 10, 'category': 'SWAP'},
            {'ticker': 'CDSO15 Curncy', 'tenor': '15Y', 'tenor_numeric': 15, 'category': 'SWAP'},
            {'ticker': 'CDSO20 Curncy', 'tenor': '20Y', 'tenor_numeric': 20, 'category': 'SWAP'},
            {'ticker': 'CDSO30 Curncy', 'tenor': '30Y', 'tenor_numeric': 30, 'category': 'SWAP'},
        ]
    },
    'AUD': {
        'curve_name': 'AUD_OIS',
        'curve_type': 'OIS',
        'methodology': 'Reserve Bank of Australia Interbank Overnight Cash Rate (AONIA) based overnight indexed swap curve',
        'primary_use': 'Risk-free rate benchmark',
        'tickers': [
            {'ticker': 'RBACOR Index', 'tenor': 'O/N', 'tenor_numeric': 1, 'category': 'RATE'},
            {'ticker': 'ADSOA Curncy', 'tenor': '1M', 'tenor_numeric': 30, 'category': 'SWAP'},
            {'ticker': 'ADSOB Curncy', 'tenor': '2M', 'tenor_numeric': 60, 'category': 'SWAP'},
            {'ticker': 'ADSOC Curncy', 'tenor': '3M', 'tenor_numeric': 90, 'category': 'SWAP'},
            {'ticker': 'ADSOD Curncy', 'tenor': '4M', 'tenor_numeric': 120, 'category': 'SWAP'},
            {'ticker': 'ADSOE Curncy', 'tenor': '5M', 'tenor_numeric': 150, 'category': 'SWAP'},
            {'ticker': 'ADSOF Curncy', 'tenor': '6M', 'tenor_numeric': 180, 'category': 'SWAP'},
            {'ticker': 'ADSOG Curncy', 'tenor': '7M', 'tenor_numeric': 210, 'category': 'SWAP'},
            {'ticker': 'ADSOH Curncy', 'tenor': '8M', 'tenor_numeric': 240, 'category': 'SWAP'},
            {'ticker': 'ADSOI Curncy', 'tenor': '9M', 'tenor_numeric': 270, 'category': 'SWAP'},
            {'ticker': 'ADSOJ Curncy', 'tenor': '10M', 'tenor_numeric': 300, 'category': 'SWAP'},
            {'ticker': 'ADSOK Curncy', 'tenor': '11M', 'tenor_numeric': 330, 'category': 'SWAP'},
            {'ticker': 'ADSO1 Curncy', 'tenor': '1Y', 'tenor_numeric': 1, 'category': 'SWAP'},
            {'ticker': 'ADSO2 Curncy', 'tenor': '2Y', 'tenor_numeric': 2, 'category': 'SWAP'},
            {'ticker': 'ADSO3 Curncy', 'tenor': '3Y', 'tenor_numeric': 3, 'category': 'SWAP'},
            {'ticker': 'ADSO4 Curncy', 'tenor': '4Y', 'tenor_numeric': 4, 'category': 'SWAP'},
            {'ticker': 'ADSO5 Curncy', 'tenor': '5Y', 'tenor_numeric': 5, 'category': 'SWAP'},
            {'ticker': 'ADSO7 Curncy', 'tenor': '7Y', 'tenor_numeric': 7, 'category': 'SWAP'},
            {'ticker': 'ADSO10 Curncy', 'tenor': '10Y', 'tenor_numeric': 10, 'category': 'SWAP'},
            {'ticker': 'ADSO15 Curncy', 'tenor': '15Y', 'tenor_numeric': 15, 'category': 'SWAP'},
            {'ticker': 'ADSO20 Curncy', 'tenor': '20Y', 'tenor_numeric': 20, 'category': 'SWAP'},
            {'ticker': 'ADSO30 Curncy', 'tenor': '30Y', 'tenor_numeric': 30, 'category': 'SWAP'},
        ]
    },
    'NZD': {
        'curve_name': 'NZD_OIS',
        'curve_type': 'OIS',
        'methodology': 'Reserve Bank of New Zealand Official Cash Rate (OCR) based overnight indexed swap curve',
        'primary_use': 'Risk-free rate benchmark',
        'tickers': [
            {'ticker': 'NZOCRS Index', 'tenor': 'O/N', 'tenor_numeric': 1, 'category': 'RATE'},
            {'ticker': 'NDSOA Curncy', 'tenor': '1M', 'tenor_numeric': 30, 'category': 'SWAP'},
            {'ticker': 'NDSOB Curncy', 'tenor': '2M', 'tenor_numeric': 60, 'category': 'SWAP'},
            {'ticker': 'NDSOC Curncy', 'tenor': '3M', 'tenor_numeric': 90, 'category': 'SWAP'},
            {'ticker': 'NDSOD Curncy', 'tenor': '4M', 'tenor_numeric': 120, 'category': 'SWAP'},
            {'ticker': 'NDSOE Curncy', 'tenor': '5M', 'tenor_numeric': 150, 'category': 'SWAP'},
            {'ticker': 'NDSOF Curncy', 'tenor': '6M', 'tenor_numeric': 180, 'category': 'SWAP'},
            {'ticker': 'NDSOG Curncy', 'tenor': '7M', 'tenor_numeric': 210, 'category': 'SWAP'},
            {'ticker': 'NDSOH Curncy', 'tenor': '8M', 'tenor_numeric': 240, 'category': 'SWAP'},
            {'ticker': 'NDSOI Curncy', 'tenor': '9M', 'tenor_numeric': 270, 'category': 'SWAP'},
            {'ticker': 'NDSOJ Curncy', 'tenor': '10M', 'tenor_numeric': 300, 'category': 'SWAP'},
            {'ticker': 'NDSOK Curncy', 'tenor': '11M', 'tenor_numeric': 330, 'category': 'SWAP'},
            {'ticker': 'NDSO1 Curncy', 'tenor': '1Y', 'tenor_numeric': 1, 'category': 'SWAP'},
            {'ticker': 'NDSO2 Curncy', 'tenor': '2Y', 'tenor_numeric': 2, 'category': 'SWAP'},
            {'ticker': 'NDSO3 Curncy', 'tenor': '3Y', 'tenor_numeric': 3, 'category': 'SWAP'},
            {'ticker': 'NDSO4 Curncy', 'tenor': '4Y', 'tenor_numeric': 4, 'category': 'SWAP'},
            {'ticker': 'NDSO5 Curncy', 'tenor': '5Y', 'tenor_numeric': 5, 'category': 'SWAP'},
            {'ticker': 'NDSO7 Curncy', 'tenor': '7Y', 'tenor_numeric': 7, 'category': 'SWAP'},
            {'ticker': 'NDSO10 Curncy', 'tenor': '10Y', 'tenor_numeric': 10, 'category': 'SWAP'},
            {'ticker': 'NDSO15 Curncy', 'tenor': '15Y', 'tenor_numeric': 15, 'category': 'SWAP'},
            {'ticker': 'NDSO20 Curncy', 'tenor': '20Y', 'tenor_numeric': 20, 'category': 'SWAP'},
            # Skip NDSO30 as it had no data
        ]
    },
    'SEK': {
        'curve_name': 'SEK_IRS',
        'curve_type': 'IRS',
        'methodology': 'Stockholm Interbank Offered Rate (STIBOR) 3M based interest rate swap curve',
        'primary_use': 'Benchmark rate curve',
        'tickers': [
            {'ticker': 'STIB1W Index', 'tenor': '1W', 'tenor_numeric': 7, 'category': 'RATE'},
            {'ticker': 'SKSW1 Curncy', 'tenor': '1Y', 'tenor_numeric': 1, 'category': 'SWAP'},
            {'ticker': 'SKSW2 Curncy', 'tenor': '2Y', 'tenor_numeric': 2, 'category': 'SWAP'},
            {'ticker': 'SKSW3 Curncy', 'tenor': '3Y', 'tenor_numeric': 3, 'category': 'SWAP'},
            {'ticker': 'SKSW4 Curncy', 'tenor': '4Y', 'tenor_numeric': 4, 'category': 'SWAP'},
            {'ticker': 'SKSW5 Curncy', 'tenor': '5Y', 'tenor_numeric': 5, 'category': 'SWAP'},
            {'ticker': 'SKSW7 Curncy', 'tenor': '7Y', 'tenor_numeric': 7, 'category': 'SWAP'},
            {'ticker': 'SKSW10 Curncy', 'tenor': '10Y', 'tenor_numeric': 10, 'category': 'SWAP'},
            {'ticker': 'SKSW15 Curncy', 'tenor': '15Y', 'tenor_numeric': 15, 'category': 'SWAP'},
            {'ticker': 'SKSW20 Curncy', 'tenor': '20Y', 'tenor_numeric': 20, 'category': 'SWAP'},
            {'ticker': 'SKSW30 Curncy', 'tenor': '30Y', 'tenor_numeric': 30, 'category': 'SWAP'},
        ]
    },
    'NOK': {
        'curve_name': 'NOK_IRS',
        'curve_type': 'IRS',
        'methodology': 'Norwegian Interbank Offered Rate (NIBOR) 6M based interest rate swap curve',
        'primary_use': 'Benchmark rate curve',
        'tickers': [
            {'ticker': 'NIBOR1W Index', 'tenor': '1W', 'tenor_numeric': 7, 'category': 'RATE'},
            {'ticker': 'NKSW1 Curncy', 'tenor': '1Y', 'tenor_numeric': 1, 'category': 'SWAP'},
            {'ticker': 'NKSW2 Curncy', 'tenor': '2Y', 'tenor_numeric': 2, 'category': 'SWAP'},
            {'ticker': 'NKSW3 Curncy', 'tenor': '3Y', 'tenor_numeric': 3, 'category': 'SWAP'},
            {'ticker': 'NKSW4 Curncy', 'tenor': '4Y', 'tenor_numeric': 4, 'category': 'SWAP'},
            {'ticker': 'NKSW5 Curncy', 'tenor': '5Y', 'tenor_numeric': 5, 'category': 'SWAP'},
            {'ticker': 'NKSW7 Curncy', 'tenor': '7Y', 'tenor_numeric': 7, 'category': 'SWAP'},
            {'ticker': 'NKSW10 Curncy', 'tenor': '10Y', 'tenor_numeric': 10, 'category': 'SWAP'},
            {'ticker': 'NKSW15 Curncy', 'tenor': '15Y', 'tenor_numeric': 15, 'category': 'SWAP'},
            {'ticker': 'NKSW20 Curncy', 'tenor': '20Y', 'tenor_numeric': 20, 'category': 'SWAP'},
            {'ticker': 'NKSW30 Curncy', 'tenor': '30Y', 'tenor_numeric': 30, 'category': 'SWAP'},
        ]
    }
}

conn = psycopg2.connect(**conn_params)
cursor = conn.cursor()

try:
    # Add each currency's curve
    for currency, config in g10_configs.items():
        print(f"\n{'='*60}")
        print(f"Adding {currency} curve...")
        print(f"{'='*60}")
        
        # Check if curve definition exists
        cursor.execute("""
            SELECT curve_name FROM rate_curve_definitions 
            WHERE curve_name = %s
        """, (config['curve_name'],))
        
        if not cursor.fetchone():
            print(f"Adding {config['curve_name']} to rate_curve_definitions...")
            cursor.execute("""
                INSERT INTO rate_curve_definitions (
                    curve_name,
                    currency_code,
                    curve_type,
                    methodology,
                    primary_use
                ) VALUES (%s, %s, %s, %s, %s)
            """, (
                config['curve_name'],
                currency,
                config['curve_type'],
                config['methodology'],
                config['primary_use']
            ))
            print(f"✓ Added {config['curve_name']} curve definition")
        
        # Add tickers
        added_count = 0
        for ticker_info in config['tickers']:
            # Check if exists
            cursor.execute("""
                SELECT bloomberg_ticker FROM bloomberg_tickers 
                WHERE bloomberg_ticker = %s
            """, (ticker_info['ticker'],))
            
            if cursor.fetchone():
                # Update to ensure correct curve assignment
                cursor.execute("""
                    UPDATE bloomberg_tickers 
                    SET curve_name = %s, category = %s
                    WHERE bloomberg_ticker = %s
                """, (config['curve_name'], ticker_info['category'], ticker_info['ticker']))
                print(f"✓ Updated {ticker_info['ticker']} to {config['curve_name']}")
            else:
                # Insert new ticker
                cursor.execute("""
                    INSERT INTO bloomberg_tickers (
                        bloomberg_ticker,
                        currency_code,
                        category,
                        tenor,
                        tenor_numeric,
                        curve_name
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    ticker_info['ticker'],
                    currency,
                    ticker_info['category'],
                    ticker_info['tenor'],
                    ticker_info['tenor_numeric'],
                    config['curve_name']
                ))
                print(f"✓ Added {ticker_info['ticker']} - {ticker_info['tenor']}")
                added_count += 1
        
        print(f"\nAdded {added_count} new tickers for {currency}")
    
    conn.commit()
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    cursor.execute("""
        SELECT currency_code, curve_name, COUNT(*) as ticker_count
        FROM bloomberg_tickers
        WHERE curve_name IN (
            'JPY_OIS', 'CHF_OIS', 'CAD_OIS', 'AUD_OIS', 
            'NZD_OIS', 'SEK_IRS', 'NOK_IRS'
        )
        GROUP BY currency_code, curve_name
        ORDER BY currency_code
    """)
    
    for row in cursor.fetchall():
        print(f"{row[0]}: {row[1]} - {row[2]} tickers")
        
except Exception as e:
    conn.rollback()
    print(f"✗ Error: {e}")
finally:
    cursor.close()
    conn.close()