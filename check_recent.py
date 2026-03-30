
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Загружаем переменные окружения
dotenv_path = os.path.join(os.path.dirname(__file__), '.env.local')
load_dotenv(dotenv_path)

def check_recent_updates():
    url = os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL")
    if not url:
        print("POSTGRES_URL not found")
        return

    conn = psycopg2.connect(url, cursor_factory=RealDictCursor)
    cur = conn.cursor()
    
    # Ищем последние 20 обновленных слов
    cur.execute("SELECT id, de, ru, article, plural, ai_checked_at FROM words ORDER BY ai_checked_at DESC NULLS LAST LIMIT 20")
    rows = cur.fetchall()
    
    print("Recent updates:")
    for row in rows:
        print(f"{row['id']}: {row['article']} {row['de']} = {row['ru']} (Plural: {row['plural']}) - {row['ai_checked_at']}")
            
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_recent_updates()
