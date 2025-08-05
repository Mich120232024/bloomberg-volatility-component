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
    # Méthode plus simple - insérer avec les mêmes valeurs que les autres tickers
    missing_tickers = [
        ('USSOA Curncy', '1M', 30),
        ('USSOB Curncy', '2M', 60),
        ('USSOC Curncy', '3M', 90)
    ]
    
    for ticker, tenor, days in missing_tickers:
        # Vérifier si existe
        cursor.execute("SELECT COUNT(*) FROM bloomberg_tickers WHERE bloomberg_ticker = %s", (ticker,))
        if cursor.fetchone()[0] == 0:
            # Copier toutes les colonnes depuis USSOD sauf ticker, tenor, tenor_numeric
            cursor.execute("""
                INSERT INTO bloomberg_tickers 
                (bloomberg_ticker, currency_code, category, subcategory, market_convention, 
                 use_cases, description, is_active, created_at, updated_at, 
                 tenor, tenor_numeric, curve_name, validation_status, format_type, 
                 format_display, data_source)
                SELECT 
                    %s, currency_code, category, subcategory, market_convention,
                    use_cases, description, is_active, NOW(), NOW(),
                    %s, %s, curve_name, validation_status, format_type,
                    format_display, data_source
                FROM bloomberg_tickers
                WHERE bloomberg_ticker = 'USSOD Curncy'
            """, (ticker, tenor, days))
            print(f"✓ Ajouté {ticker} ({tenor})")
        else:
            print(f"- {ticker} existe déjà")
    
    conn.commit()
    print("\n✓ Tickers 1M, 2M, 3M ajoutés avec succès")
    
except Exception as e:
    conn.rollback()
    print(f"✗ Erreur: {e}")
finally:
    cursor.close()
    conn.close()