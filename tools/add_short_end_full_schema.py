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
    # Get a complete row from USSOD to copy all fields
    cursor.execute("""
        SELECT * FROM bloomberg_tickers 
        WHERE bloomberg_ticker = 'USSOD Curncy'
    """)
    
    base_row = cursor.fetchone()
    print(f"Base row has {len(base_row)} columns")
    
    # Get column names
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'bloomberg_tickers'
        ORDER BY ordinal_position
    """)
    
    columns = [row[0] for row in cursor.fetchall()]
    print(f"Table has {len(columns)} columns")
    
    # Find indices for fields we need to change
    ticker_idx = columns.index('bloomberg_ticker')
    tenor_idx = columns.index('tenor') 
    tenor_numeric_idx = columns.index('tenor_numeric')
    created_idx = columns.index('created_at')
    updated_idx = columns.index('updated_at')
    id_idx = columns.index('id')
    
    new_tickers = [
        ('USSOA Curncy', '1M', 30.0),
        ('USSOB Curncy', '2M', 60.0),
        ('USSOC Curncy', '3M', 90.0)
    ]
    
    for ticker, tenor, days in new_tickers:
        # Check if exists
        cursor.execute("SELECT COUNT(*) FROM bloomberg_tickers WHERE bloomberg_ticker = %s", (ticker,))
        if cursor.fetchone()[0] == 0:
            # Copy base row and modify specific fields
            new_row = list(base_row)
            new_row[id_idx] = None  # Auto-increment
            new_row[ticker_idx] = ticker
            new_row[tenor_idx] = tenor
            new_row[tenor_numeric_idx] = days
            new_row[created_idx] = None  # Will use NOW()
            new_row[updated_idx] = None  # Will use NOW()
            
            # Build INSERT with all columns except id
            non_id_columns = [col for col in columns if col != 'id']
            non_id_values = [new_row[i] for i, col in enumerate(columns) if col != 'id']
            
            placeholders = []
            final_values = []
            
            for i, (col, val) in enumerate(zip(non_id_columns, non_id_values)):
                if col in ['created_at', 'updated_at']:
                    placeholders.append('NOW()')
                else:
                    placeholders.append('%s')
                    final_values.append(val)
            
            query = f"""
                INSERT INTO bloomberg_tickers ({', '.join(non_id_columns)})
                VALUES ({', '.join(placeholders)})
            """
            
            cursor.execute(query, final_values)
            print(f"Added {ticker} ({tenor})")
        else:
            print(f"Skipped {ticker} (exists)")
    
    conn.commit()
    print("Success!")
    
except Exception as e:
    conn.rollback()
    print(f"Error: {e}")
    raise
finally:
    cursor.close()
    conn.close()