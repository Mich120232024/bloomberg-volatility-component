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
    # Utiliser une requête SQL directe pour copier depuis USSOD et modifier
    missing_tickers = [
        ('USSOA Curncy', '1M', 30),
        ('USSOB Curncy', '2M', 60),
        ('USSOC Curncy', '3M', 90)
    ]
    
    for ticker, tenor, days in missing_tickers:
        # Vérifier si existe
        cursor.execute("SELECT COUNT(*) FROM bloomberg_tickers WHERE bloomberg_ticker = %s", (ticker,))
        if cursor.fetchone()[0] == 0:
            # Copier depuis USSOD en changeant ticker, tenor et tenor_numeric
            cursor.execute("""
                INSERT INTO bloomberg_tickers 
                SELECT 
                    nextval('bloomberg_tickers_id_seq'),  -- nouveau ID
                    %s,  -- nouveau ticker
                    currency_code,
                    category,
                    subcategory,
                    market_convention,
                    use_cases,
                    description,
                    is_active,
                    NOW(),  -- created_at
                    NOW(),  -- updated_at
                    security_name,
                    asset_class,
                    exchange,
                    last_price,
                    price_change,
                    validation_status,
                    validation_errors,
                    format_type,
                    format_display,
                    reference_rate,
                    index_family,
                    quote_type,
                    day_count_convention,
                    fixing_source,
                    data_source,
                    fetch_priority,
                    requires_subscription,
                    notes,
                    metadata,
                    %s,  -- nouveau tenor
                    %s,  -- nouveau tenor_numeric  
                    curve_name,
                    instrument_type
                FROM bloomberg_tickers
                WHERE bloomberg_ticker = 'USSOD Curncy'
            """, (ticker, tenor, days))
            print(f"✓ Ajouté {ticker} ({tenor})")
        else:
            print(f"- {ticker} existe déjà")
    
    conn.commit()
    print("\n✓ Mise à jour terminée")
    
except Exception as e:
    conn.rollback()
    print(f"✗ Erreur: {e}")
finally:
    cursor.close()
    conn.close()