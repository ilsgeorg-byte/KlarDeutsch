
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Загружаем переменные окружения
dotenv_path = os.path.join(os.path.dirname(__file__), '.env.local')
load_dotenv(dotenv_path)

def debug_ids():
    url = os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL")
    if not url:
        print("POSTGRES_URL not found")
        return

    conn = psycopg2.connect(url, cursor_factory=RealDictCursor)
    cur = conn.cursor()
    
    cur.execute("SELECT id, de, article, ru FROM words WHERE id IN (6712, 5393)")
    rows = cur.fetchall()
    for row in rows:
        print(f"ID: {row['id']} | DE: '{row['de']}' | Article: '{row['article']}' | RU: '{row['ru']}'")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    debug_ids()
