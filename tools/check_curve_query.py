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

conn = psycopg2.connect(**conn_params)
cursor = conn.cursor()

try:
    # Test exact query from gateway
    cursor.execute("""
        SELECT rcd.curve_name, rcd.curve_type, rcd.methodology, rcd.primary_use,
               bt.bloomberg_ticker, bt.description, bt.tenor, bt.tenor_numeric
        FROM rate_curve_definitions rcd
        JOIN bloomberg_tickers bt ON bt.curve_name = rcd.curve_name
        WHERE rcd.currency_code = 'USD' AND rcd.curve_type = 'OIS'
        ORDER BY bt.tenor_numeric
    """)
    
    results = cursor.fetchall()
    print(f"Query retourne {len(results)} lignes")
    
    # Afficher les premiers résultats
    for row in results[:5]:
        print(f"  {row[4]:15} {row[6]:>4} -> {row[7]} jours")
        
    # Vérifier si USSOA, USSOB, USSOC sont dans bloomberg_tickers
    cursor.execute("""
        SELECT bloomberg_ticker, curve_name, tenor, tenor_numeric
        FROM bloomberg_tickers
        WHERE bloomberg_ticker IN ('USSOA Curncy', 'USSOB Curncy', 'USSOC Curncy')
    """)
    
    print("\n1M, 2M, 3M dans bloomberg_tickers:")
    for row in cursor.fetchall():
        print(f"  {row[0]:15} curve_name={row[1]} tenor={row[2]} days={row[3]}")
        
except Exception as e:
    print(f"Erreur: {e}")
finally:
    cursor.close()
    conn.close()