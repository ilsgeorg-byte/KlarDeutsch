import os
import psycopg2
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.local')
load_dotenv(dotenv_path)

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'words'
    ORDER BY ordinal_position;
""")

print("📋 Столбцы таблицы 'words':")
for col in cur.fetchall():
    print(f"  - {col[0]}  ({col[1]})")

cur.close()
conn.close()
