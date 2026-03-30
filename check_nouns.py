
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Загружаем переменные окружения
dotenv_path = os.path.join(os.path.dirname(__file__), '.env.local')
load_dotenv(dotenv_path)

def check_nouns_no_plural():
    url = os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL")
    if not url:
        print("POSTGRES_URL not found")
        return

    conn = psycopg2.connect(url, cursor_factory=RealDictCursor)
    cur = conn.cursor()
    
    # Ищем существительные (с артиклем) без множественного числа
    # Исключаем неисчисляемые (Singularetantum), если AI поставил '-'
    cur.execute("""
        SELECT id, de, article, ru, plural, ai_checked_at 
        FROM words 
        WHERE article IN ('der', 'die', 'das') 
          AND (plural IS NULL OR plural = '' OR plural = 'None')
        ORDER BY ai_checked_at DESC NULLS LAST
        LIMIT 50
    """)
    rows = cur.fetchall()
    
    if rows:
        print(f"Found {len(rows)} nouns with missing plural:")
        for row in rows:
            print(f"ID: {row['id']}, DE: {row['article']} {row['de']}, RU: {row['ru']}, Checked: {row['ai_checked_at']}")
    else:
        print("No nouns with missing plural found.")
            
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_nouns_no_plural()
