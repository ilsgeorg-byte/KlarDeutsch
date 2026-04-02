import os
import psycopg2
from dotenv import load_dotenv

load_dotenv('.env.local')
url = os.getenv("DATABASE_URL")

def inspect():
    conn = psycopg2.connect(url)
    cur = conn.cursor()
    
    # Запрос на поиск всех внешних ключей, ссылающихся на таблицу 'words'
    query = """
    SELECT
        tc.table_name, 
        kcu.column_name, 
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name 
    FROM 
        information_schema.table_constraints AS tc 
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
          AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_name = tc.constraint_name
          AND ccu.table_schema = tc.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY' AND ccu.table_name='words';
    """
    
    cur.execute(query)
    rows = cur.fetchall()
    print("Found tables referencing 'words':")
    for row in rows:
        print(f"Table: {row[0]}, Column: {row[1]} -> references {row[2]}.{row[3]}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    inspect()
