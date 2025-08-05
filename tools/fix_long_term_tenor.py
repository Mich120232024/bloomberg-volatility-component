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
    # Corriger les tenor_numeric pour 15Y, 20Y, 30Y
    fixes = [
        ('USSO15 Curncy', 15.0),  # Garder comme années
        ('USSO20 Curncy', 20.0),  # Le gateway convertira
        ('USSO30 Curncy', 30.0)   # en jours
    ]
    
    for ticker, years in fixes:
        cursor.execute("""
            UPDATE bloomberg_tickers 
            SET tenor_numeric = %s
            WHERE bloomberg_ticker = %s
        """, (years, ticker))
        print(f"✓ Mis à jour {ticker} -> {years} ans")
    
    conn.commit()
    print("\n✓ tenor_numeric corrigés pour 15Y, 20Y, 30Y")
    
except Exception as e:
    conn.rollback()
    print(f"✗ Erreur: {e}")
finally:
    cursor.close()
    conn.close()