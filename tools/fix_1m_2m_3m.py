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
    # Mettre à jour curve_name, tenor et tenor_numeric pour 1M, 2M, 3M
    updates = [
        ('USSOA Curncy', '1M', 30),
        ('USSOB Curncy', '2M', 60),
        ('USSOC Curncy', '3M', 90)
    ]
    
    for ticker, tenor, days in updates:
        cursor.execute("""
            UPDATE bloomberg_tickers
            SET curve_name = 'USD_OIS',
                tenor = %s,
                tenor_numeric = %s
            WHERE bloomberg_ticker = %s
        """, (tenor, days, ticker))
        print(f"✓ Mis à jour {ticker}: curve_name=USD_OIS, tenor={tenor}, days={days}")
    
    conn.commit()
    print("\n✓ Corrections appliquées!")
    
    # Vérifier
    cursor.execute("""
        SELECT bloomberg_ticker, curve_name, tenor, tenor_numeric
        FROM bloomberg_tickers
        WHERE curve_name = 'USD_OIS' AND tenor_numeric <= 365
        ORDER BY tenor_numeric
    """)
    
    print("\nCourbe USD OIS short-end:")
    for row in cursor.fetchall():
        print(f"  {row[0]:15} {row[2]:>4} -> {row[3]:>4.0f} jours")
        
except Exception as e:
    conn.rollback()
    print(f"✗ Erreur: {e}")
finally:
    cursor.close()
    conn.close()