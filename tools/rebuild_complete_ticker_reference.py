#!/usr/bin/env python3
"""
Rebuild ticker_reference with complete tenor structure for all currencies
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from yield_curve_db_endpoint import get_database_connection

# Complete tenor structure requested
TENOR_STRUCTURE = [
    ('1D', '1D', 1),
    ('1W', '1W', 7),
    ('2W', '2W', 14),
    ('3W', '3W', 21),
    ('1M', '1M', 30),
    ('2M', '2M', 60),
    ('3M', '3M', 90),
    ('6M', '6M', 180),
    ('9M', '9M', 270),
    ('12M', '1Y', 365),  # 12M = 1Y
    ('15M', '15M', 456),
    ('18M', '18M', 548),
    ('21M', '21M', 639),
    ('24M', '2Y', 730),  # 24M = 2Y
    ('3Y', '3Y', 1095),
    ('4Y', '4Y', 1460),
    ('5Y', '5Y', 1825),
    ('7Y', '7Y', 2555),
    ('10Y', '10Y', 3650),
    ('15Y', '15Y', 5475),
    ('20Y', '20Y', 7300),  # Assuming 29Y was typo for 20Y
    ('25Y', '25Y', 9125),
    ('30Y', '30Y', 10950)
]

# OIS ticker patterns - mapping to Bloomberg conventions
CURRENCY_PATTERNS = {
    'USD': {
        'curve_name': 'USD_SOFR_OIS',
        'overnight': 'SOFRRATE Index',
        'patterns': {
            '1D': 'USSW1Z Curncy',     # 1 day SOFR
            '1W': 'USSW1 Curncy',      # 1 week
            '2W': 'USSW2 Curncy',      # 2 week
            '3W': 'USSW3 Curncy',      # 3 week
            '1M': 'USSOA Curncy',      # 1 month
            '2M': 'USSOB Curncy',      # 2 month
            '3M': 'USSOC Curncy',      # 3 month
            '6M': 'USSOF Curncy',      # 6 month
            '9M': 'USSOI Curncy',      # 9 month
            '12M': 'USSO1 Curncy',     # 1 year
            '15M': 'USSO15M Curncy',   # 15 month
            '18M': 'USSO18M Curncy',   # 18 month
            '21M': 'USSO21M Curncy',   # 21 month
            '24M': 'USSO2 Curncy',     # 2 year
            '3Y': 'USSO3 Curncy',
            '4Y': 'USSO4 Curncy',
            '5Y': 'USSO5 Curncy',
            '7Y': 'USSO7 Curncy',
            '10Y': 'USSO10 Curncy',
            '15Y': 'USSO15 Curncy',
            '20Y': 'USSO20 Curncy',
            '25Y': 'USSO25 Curncy',
            '30Y': 'USSO30 Curncy'
        }
    },
    'EUR': {
        'curve_name': 'EUR_ESTR_OIS',
        'overnight': 'ESTRON Index',
        'patterns': {
            '1D': 'EESW1Z Curncy',
            '1W': 'EESWEA Curncy',
            '2W': 'EESWEB Curncy',
            '3W': 'EESWEC Curncy',
            '1M': 'EESWE1M Curncy',
            '2M': 'EESWE2M Curncy',
            '3M': 'EESWE3M Curncy',
            '6M': 'EESWE6M Curncy',
            '9M': 'EESWE9M Curncy',
            '12M': 'EESWE1 Curncy',
            '15M': 'EESWE15M Curncy',
            '18M': 'EESWE18M Curncy',
            '21M': 'EESWE21M Curncy',
            '24M': 'EESWE2 Curncy',
            '3Y': 'EESWE3 Curncy',
            '4Y': 'EESWE4 Curncy',
            '5Y': 'EESWE5 Curncy',
            '7Y': 'EESWE7 Curncy',
            '10Y': 'EESWE10 Curncy',
            '15Y': 'EESWE15 Curncy',
            '20Y': 'EESWE20 Curncy',
            '25Y': 'EESWE25 Curncy',
            '30Y': 'EESWE30 Curncy'
        }
    },
    'GBP': {
        'curve_name': 'GBP_SONIA_OIS',
        'overnight': 'SONIA Index',
        'patterns': {
            '1D': 'BPSW1Z Curncy',
            '1W': 'BPSWA Curncy',
            '2W': 'BPSWB Curncy',
            '3W': 'BPSWC Curncy',
            '1M': 'SONIOA Curncy',
            '2M': 'SONIOB Curncy',
            '3M': 'SONIOC Curncy',
            '6M': 'SONIOF Curncy',
            '9M': 'SONIOI Curncy',
            '12M': 'SONIO1 Curncy',
            '15M': 'SONIO15M Curncy',
            '18M': 'SONIO18M Curncy',
            '21M': 'SONIO21M Curncy',
            '24M': 'SONIO2 Curncy',
            '3Y': 'SONIO3 Curncy',
            '4Y': 'SONIO4 Curncy',
            '5Y': 'SONIO5 Curncy',
            '7Y': 'SONIO7 Curncy',
            '10Y': 'SONIO10 Curncy',
            '15Y': 'SONIO15 Curncy',
            '20Y': 'SONIO20 Curncy',
            '25Y': 'SONIO25 Curncy',
            '30Y': 'SONIO30 Curncy'
        }
    },
    'JPY': {
        'curve_name': 'JPY_TONAR_OIS',
        'overnight': 'MUTKCALM Index',
        'patterns': {
            '1D': 'JYSW1Z Curncy',
            '1W': 'JYSWA Curncy',
            '2W': 'JYSWB Curncy',
            '3W': 'JYSWC Curncy',
            '1M': 'JYSOA Curncy',
            '2M': 'JYSOB Curncy',
            '3M': 'JYSOC Curncy',
            '6M': 'JYSOF Curncy',
            '9M': 'JYSOI Curncy',
            '12M': 'JYSO1 Curncy',
            '15M': 'JYSO15M Curncy',
            '18M': 'JYSO18M Curncy',
            '21M': 'JYSO21M Curncy',
            '24M': 'JYSO2 Curncy',
            '3Y': 'JYSO3 Curncy',
            '4Y': 'JYSO4 Curncy',
            '5Y': 'JYSO5 Curncy',
            '7Y': 'JYSO7 Curncy',
            '10Y': 'JYSO10 Curncy',
            '15Y': 'JYSO15 Curncy',
            '20Y': 'JYSO20 Curncy',
            '25Y': 'JYSO25 Curncy',
            '30Y': 'JYSO30 Curncy'
        }
    },
    'CHF': {
        'curve_name': 'CHF_SARON_OIS',
        'overnight': 'SRFRRATE Index',
        'patterns': {
            '1D': 'SFSW1Z Curncy',
            '1W': 'SFSWA Curncy',
            '2W': 'SFSWB Curncy',
            '3W': 'SFSWC Curncy',
            '1M': 'SSARONA Curncy',
            '2M': 'SSARONB Curncy',
            '3M': 'SSARONC Curncy',
            '6M': 'SSARONF Curncy',
            '9M': 'SSARONI Curncy',
            '12M': 'SSARON1 Curncy',
            '15M': 'SSARON15M Curncy',
            '18M': 'SSARON18M Curncy',
            '21M': 'SSARON21M Curncy',
            '24M': 'SSARON2 Curncy',
            '3Y': 'SSARON3 Curncy',
            '4Y': 'SSARON4 Curncy',
            '5Y': 'SSARON5 Curncy',
            '7Y': 'SSARON7 Curncy',
            '10Y': 'SSARON10 Curncy',
            '15Y': 'SSARON15 Curncy',
            '20Y': 'SSARON20 Curncy',
            '25Y': 'SSARON25 Curncy',
            '30Y': 'SSARON30 Curncy'
        }
    },
    'CAD': {
        'curve_name': 'CAD_CORRA_OIS',
        'overnight': 'CAONREPO Index',
        'patterns': {
            '1D': 'CDSW1Z Curncy',
            '1W': 'CDSWA Curncy',
            '2W': 'CDSWB Curncy',
            '3W': 'CDSWC Curncy',
            '1M': 'CDSOA Curncy',
            '2M': 'CDSOB Curncy',
            '3M': 'CDSOC Curncy',
            '6M': 'CDSOF Curncy',
            '9M': 'CDSOI Curncy',
            '12M': 'CDSO1 Curncy',
            '15M': 'CDSO15M Curncy',
            '18M': 'CDSO18M Curncy',
            '21M': 'CDSO21M Curncy',
            '24M': 'CDSO2 Curncy',
            '3Y': 'CDSO3 Curncy',
            '4Y': 'CDSO4 Curncy',
            '5Y': 'CDSO5 Curncy',
            '7Y': 'CDSO7 Curncy',
            '10Y': 'CDSO10 Curncy',
            '15Y': 'CDSO15 Curncy',
            '20Y': 'CDSO20 Curncy',
            '25Y': 'CDSO25 Curncy',
            '30Y': 'CDSO30 Curncy'
        }
    },
    'AUD': {
        'curve_name': 'AUD_AONIA_OIS',
        'overnight': 'RBACOR Index',
        'patterns': {
            '1D': 'ADSW1Z Curncy',
            '1W': 'ADSWA Curncy',
            '2W': 'ADSWB Curncy',
            '3W': 'ADSWC Curncy',
            '1M': 'RBAOA Curncy',
            '2M': 'RBAOB Curncy',
            '3M': 'RBAOC Curncy',
            '6M': 'RBAOF Curncy',
            '9M': 'RBAOI Curncy',
            '12M': 'RBAO1 Curncy',
            '15M': 'RBAO15M Curncy',
            '18M': 'RBAO18M Curncy',
            '21M': 'RBAO21M Curncy',
            '24M': 'RBAO2 Curncy',
            '3Y': 'RBAO3 Curncy',
            '4Y': 'RBAO4 Curncy',
            '5Y': 'RBAO5 Curncy',
            '7Y': 'RBAO7 Curncy',
            '10Y': 'RBAO10 Curncy',
            '15Y': 'RBAO15 Curncy',
            '20Y': 'RBAO20 Curncy',
            '25Y': 'RBAO25 Curncy',
            '30Y': 'RBAO30 Curncy'
        }
    },
    'NZD': {
        'curve_name': 'NZD_NZIONA_OIS',
        'overnight': 'NZOCRS Index',
        'patterns': {
            '1D': 'NDSW1Z Curncy',
            '1W': 'NDSWA Curncy',
            '2W': 'NDSWB Curncy',
            '3W': 'NDSWC Curncy',
            '1M': 'NDSOA Curncy',
            '2M': 'NDSOB Curncy',
            '3M': 'NDSOC Curncy',
            '6M': 'NDSOF Curncy',
            '9M': 'NDSOI Curncy',
            '12M': 'NDSO1 Curncy',
            '15M': 'NDSO15M Curncy',
            '18M': 'NDSO18M Curncy',
            '21M': 'NDSO21M Curncy',
            '24M': 'NDSO2 Curncy',
            '3Y': 'NDSO3 Curncy',
            '4Y': 'NDSO4 Curncy',
            '5Y': 'NDSO5 Curncy',
            '7Y': 'NDSO7 Curncy',
            '10Y': 'NDSO10 Curncy',
            '15Y': 'NDSO15 Curncy',
            '20Y': 'NDSO20 Curncy',
            '25Y': 'NDSO25 Curncy',
            '30Y': 'NDSO30 Curncy'
        }
    },
    'SEK': {
        'curve_name': 'SEK_STIBOR_OIS',
        'overnight': 'SEONIA Index',
        'patterns': {
            '1D': 'SKSW1Z Curncy',
            '1W': 'SKSWA Curncy',
            '2W': 'SKSWB Curncy',
            '3W': 'SKSWC Curncy',
            '1M': 'SKSOA Curncy',
            '2M': 'SKSOB Curncy',
            '3M': 'SKSOC Curncy',
            '6M': 'SKSOF Curncy',
            '9M': 'SKSOI Curncy',
            '12M': 'SKSO1 Curncy',
            '15M': 'SKSO15M Curncy',
            '18M': 'SKSO18M Curncy',
            '21M': 'SKSO21M Curncy',
            '24M': 'SKSO2 Curncy',
            '3Y': 'SKSO3 Curncy',
            '4Y': 'SKSO4 Curncy',
            '5Y': 'SKSO5 Curncy',
            '7Y': 'SKSO7 Curncy',
            '10Y': 'SKSO10 Curncy',
            '15Y': 'SKSO15 Curncy',
            '20Y': 'SKSO20 Curncy',
            '25Y': 'SKSO25 Curncy',
            '30Y': 'SKSO30 Curncy'
        }
    },
    'NOK': {
        'curve_name': 'NOK_NOWA_OIS',
        'overnight': 'NOWA Index',
        'patterns': {
            '1D': 'NKSW1Z Curncy',
            '1W': 'NKSWA Curncy',
            '2W': 'NKSWB Curncy',
            '3W': 'NKSWC Curncy',
            '1M': 'NKSOA Curncy',
            '2M': 'NKSOB Curncy',
            '3M': 'NKSOC Curncy',
            '6M': 'NKSOF Curncy',
            '9M': 'NKSOI Curncy',
            '12M': 'NKSO1 Curncy',
            '15M': 'NKSO15M Curncy',
            '18M': 'NKSO18M Curncy',
            '21M': 'NKSO21M Curncy',
            '24M': 'NKSO2 Curncy',
            '3Y': 'NKSO3 Curncy',
            '4Y': 'NKSO4 Curncy',
            '5Y': 'NKSO5 Curncy',
            '7Y': 'NKSO7 Curncy',
            '10Y': 'NKSO10 Curncy',
            '15Y': 'NKSO15 Curncy',
            '20Y': 'NKSO20 Curncy',
            '25Y': 'NKSO25 Curncy',
            '30Y': 'NKSO30 Curncy'
        }
    },
    'BRL': {
        'curve_name': 'BRL_SELIC_OIS',
        'overnight': 'BZDIOVRA Index',
        'patterns': {
            '1D': 'BPSW1Z Curncy',
            '1W': 'BPSWA Curncy',
            '2W': 'BPSWB Curncy',
            '3W': 'BPSWC Curncy',
            '1M': 'BPSOA Curncy',
            '2M': 'BPSOB Curncy',
            '3M': 'BPSOC Curncy',
            '6M': 'BPSOF Curncy',
            '9M': 'BPSOI Curncy',
            '12M': 'BPSO1 Curncy',
            '15M': 'BPSO15M Curncy',
            '18M': 'BPSO18M Curncy',
            '21M': 'BPSO21M Curncy',
            '24M': 'BPSO2 Curncy',
            '3Y': 'BPSO3 Curncy',
            '4Y': 'BPSO4 Curncy',
            '5Y': 'BPSO5 Curncy',
            '7Y': 'BPSO7 Curncy',
            '10Y': 'BPSO10 Curncy',
            '15Y': 'BPSO15 Curncy',
            '20Y': 'BPSO20 Curncy',
            '25Y': 'BPSO25 Curncy',
            '30Y': 'BPSO30 Curncy'
        }
    }
}

def rebuild_ticker_reference():
    """Rebuild ticker_reference with complete tenor structure"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        # Clear existing data
        cursor.execute("DELETE FROM ticker_reference")
        print(f"Cleared {cursor.rowcount} existing rows")
        
        total_added = 0
        
        for currency, config in CURRENCY_PATTERNS.items():
            print(f"\n{currency} ({config['curve_name']}):")
            
            # Add overnight rate
            cursor.execute("""
                INSERT INTO ticker_reference 
                (bloomberg_ticker, currency_code, instrument_type, curve_name, is_active)
                VALUES (%s, %s, %s, %s, %s)
            """, (config['overnight'], currency, 'overnight', config['curve_name'], True))
            print(f"  Added overnight: {config['overnight']}")
            total_added += 1
            
            # Add all tenors
            for code, label, days in TENOR_STRUCTURE:
                ticker = config['patterns'].get(code, f"UNKNOWN_{code}")
                
                cursor.execute("""
                    INSERT INTO ticker_reference 
                    (bloomberg_ticker, currency_code, instrument_type, curve_name, is_active)
                    VALUES (%s, %s, %s, %s, %s)
                """, (ticker, currency, 'ois', config['curve_name'], True))
                
                print(f"  {code}: {ticker}")
                total_added += 1
        
        conn.commit()
        print(f"\n✅ Added {total_added} total tickers")
        
        # Verify
        cursor.execute("""
            SELECT currency_code, COUNT(*) 
            FROM ticker_reference 
            GROUP BY currency_code 
            ORDER BY currency_code
        """)
        
        print("\n=== FINAL COUNTS ===")
        for row in cursor.fetchall():
            print(f"{row[0]}: {row[1]} tickers (should be 24)")
            
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    rebuild_ticker_reference()