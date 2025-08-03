#!/usr/bin/env python3
import psycopg2
from datetime import datetime

conn_params = {
    'host': 'gzcdevserver.postgres.database.azure.com',
    'database': 'gzc_platform',
    'user': 'mikael',
    'port': 5432,
    'password': 'Ii89rra137+*',
    'sslmode': 'require'
}

# Liste complète des tickers USD OIS 1M-30Y
usd_ois_tickers = [
    # Mensuels  
    ('USSOA Curncy', '1M', 30),
    ('USSOB Curncy', '2M', 60),
    ('USSOC Curncy', '3M', 90),
    ('USSOD Curncy', '4M', 120),
    ('USSOE Curncy', '5M', 150),
    ('USSOF Curncy', '6M', 180),
    ('USSOG Curncy', '7M', 210),
    ('USSOH Curncy', '8M', 240),
    ('USSOI Curncy', '9M', 270),
    ('USSOJ Curncy', '10M', 300),
    ('USSOK Curncy', '11M', 330),
    # Annuels
    ('USSO1 Curncy', '1Y', 365),
    ('USSO2 Curncy', '2Y', 730),
    ('USSO3 Curncy', '3Y', 1095),
    ('USSO4 Curncy', '4Y', 1460),
    ('USSO5 Curncy', '5Y', 1825),
    ('USSO6 Curncy', '6Y', 2190),
    ('USSO7 Curncy', '7Y', 2555),
    ('USSO8 Curncy', '8Y', 2920),
    ('USSO9 Curncy', '9Y', 3285),
    ('USSO10 Curncy', '10Y', 3650),
    ('USSO15 Curncy', '15Y', 5475),
    ('USSO20 Curncy', '20Y', 7300),
    ('USSO30 Curncy', '30Y', 10950)
]

conn = psycopg2.connect(**conn_params)
cursor = conn.cursor()

try:
    # D'abord, obtenir un exemple complet de row pour copier le schema
    cursor.execute("""
        SELECT * FROM bloomberg_tickers 
        WHERE bloomberg_ticker LIKE 'USSO%' AND curve_name = 'USD_OIS'
        LIMIT 1
    """)
    
    sample_row = cursor.fetchone()
    
    if not sample_row:
        print("Aucun ticker USD OIS existant pour copier le schema")
        # Créer avec les champs minimaux requis
        for ticker, tenor, days in usd_ois_tickers:
            cursor.execute("""
                SELECT COUNT(*) FROM bloomberg_tickers 
                WHERE bloomberg_ticker = %s
            """, (ticker,))
            
            if cursor.fetchone()[0] == 0:
                # Trouver les champs requis
                cursor.execute("""
                    SELECT column_name, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'bloomberg_tickers' 
                    AND is_nullable = 'NO'
                    AND column_default IS NULL
                    ORDER BY ordinal_position
                """)
                
                required_cols = [row[0] for row in cursor.fetchall() if row[0] != 'id']
                print(f"Champs requis: {required_cols}")
                
                # Pour l'instant, skip l'insertion complexe
                print(f"SKIP {ticker} - schema trop complexe")
    else:
        # Obtenir les noms de colonnes
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'bloomberg_tickers'
            ORDER BY ordinal_position
        """)
        
        columns = [row[0] for row in cursor.fetchall()]
        
        # Pour chaque ticker, vérifier et insérer
        for ticker, tenor, days in usd_ois_tickers:
            cursor.execute("""
                SELECT COUNT(*) FROM bloomberg_tickers 
                WHERE bloomberg_ticker = %s
            """, (ticker,))
            
            if cursor.fetchone()[0] == 0:
                # Copier sample_row et modifier
                new_row = list(sample_row)
                
                # Trouver les indices des colonnes à modifier
                ticker_idx = columns.index('bloomberg_ticker')
                tenor_idx = columns.index('tenor')
                tenor_numeric_idx = columns.index('tenor_numeric')
                
                new_row[ticker_idx] = ticker
                new_row[tenor_idx] = tenor
                new_row[tenor_numeric_idx] = days
                
                # Pour l'instant, juste afficher ce qu'on ferait
                print(f"À créer: {ticker} ({tenor}) - {days} jours")
            else:
                print(f"Existe déjà: {ticker}")
    
    # Afficher l'état actuel
    cursor.execute("""
        SELECT bloomberg_ticker, tenor, tenor_numeric 
        FROM bloomberg_tickers 
        WHERE curve_name = 'USD_OIS'
        ORDER BY 
        CASE 
            WHEN tenor_numeric < 365 THEN tenor_numeric
            WHEN tenor_numeric < 1000 THEN tenor_numeric  
            ELSE tenor_numeric
        END
    """)
    
    print("\n=== COURBE USD OIS ACTUELLE ===")
    for row in cursor.fetchall():
        print(f"{row[0]:15} {row[1]:>4} -> {row[2]:>6.0f} jours")
        
except Exception as e:
    print(f"Erreur: {e}")
    conn.rollback()
finally:
    cursor.close()
    conn.close()