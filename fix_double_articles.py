
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import re

# Загружаем переменные окружения
dotenv_path = os.path.join(os.path.dirname(__file__), '.env.local')
load_dotenv(dotenv_path)

def fix_double_articles():
    url = os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL")
    if not url:
        print("POSTGRES_URL not found")
        return

    conn = psycopg2.connect(url, cursor_factory=RealDictCursor)
    cur = conn.cursor()
    
    # Ищем слова, начинающиеся с "der der ", "die die ", "das das "
    cur.execute("""
        SELECT id, de, article FROM words 
        WHERE de ~* '^(der|die|das)\\s+(der|die|das)\\s+'
    """)
    rows = cur.fetchall()
    
    if rows:
        print(f"Found {len(rows)} words with double articles:")
        for row in rows:
            old_de = row['de']
            # Убираем лишний артикль в начале
            new_de = re.sub(r'^(der|die|das)\s+(der|die|das)\s+', r'\1 ', old_de, flags=re.IGNORECASE)
            print(f"ID: {row['id']}, DE: {old_de} -> {new_de}")
            
            cur.execute("UPDATE words SET de = %s WHERE id = %s", (new_de, row['id']))
    else:
        print("No double articles found.")

    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    fix_double_articles()
