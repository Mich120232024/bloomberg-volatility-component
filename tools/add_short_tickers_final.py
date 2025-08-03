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
    # D'abord, voir quelles colonnes sont NOT NULL
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'bloomberg_tickers' 
        AND is_nullable = 'NO'
        AND column_default IS NULL
        AND column_name != 'id'
    """)
    
    required_cols = [row[0] for row in cursor.fetchall()]
    print(f"Colonnes obligatoires: {required_cols}")
    
    # Obtenir les valeurs depuis USSOD pour ces colonnes
    cursor.execute(f"""
        SELECT {', '.join(required_cols)}
        FROM bloomberg_tickers
        WHERE bloomberg_ticker = 'USSOD Curncy'
    """)
    
    base_values = cursor.fetchone()
    if base_values:
        print(f"Valeurs de base: {dict(zip(required_cols, base_values))}")
        
        # Créer les nouveaux tickers
        for ticker, tenor, days in [('USSOA Curncy', '1M', 30), ('USSOB Curncy', '2M', 60), ('USSOC Curncy', '3M', 90)]:
            cursor.execute("SELECT COUNT(*) FROM bloomberg_tickers WHERE bloomberg_ticker = %s", (ticker,))
            if cursor.fetchone()[0] == 0:
                # Préparer les valeurs
                values = list(base_values)
                
                # Remplacer ticker, tenor, tenor_numeric s'ils sont dans required_cols
                if 'bloomberg_ticker' in required_cols:
                    values[required_cols.index('bloomberg_ticker')] = ticker
                if 'tenor' in required_cols:
                    values[required_cols.index('tenor')] = tenor
                if 'tenor_numeric' in required_cols:
                    values[required_cols.index('tenor_numeric')] = days
                    
                # Ajouter les colonnes avec defaults
                all_cols = required_cols + ['created_at', 'updated_at']
                all_values = values + ['NOW()', 'NOW()']
                
                # Construire la requête
                placeholders = ['%s'] * len(values) + ['NOW()', 'NOW()']
                query = f"""
                    INSERT INTO bloomberg_tickers ({', '.join(all_cols)})
                    VALUES ({', '.join(placeholders)})
                """
                
                cursor.execute(query, values)
                print(f"✓ Ajouté {ticker}")
    
    conn.commit()
    print("\n✓ Terminé!")
    
except Exception as e:
    conn.rollback()
    print(f"✗ Erreur: {e}")
    import traceback
    traceback.print_exc()
finally:
    cursor.close()
    conn.close()