
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Загружаем переменные окружения
dotenv_path = os.path.join(os.path.dirname(__file__), '.env.local')
load_dotenv(dotenv_path)

def check_word():
    url = os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL")
    if not url:
        print("POSTGRES_URL not found")
        return

    conn = psycopg2.connect(url, cursor_factory=RealDictCursor)
    cur = conn.cursor()
    
    # Ищем слово Schild (игнорируя регистр для надежности, хотя в БД обычно с большой буквы существительные)
    cur.execute("SELECT * FROM words WHERE de ILIKE 'Schild' OR de ILIKE 'das Schild' OR de ILIKE 'der Schild'")
    rows = cur.fetchall()
    
    if not rows:
        print("Word 'Schild' not found in database")
    else:
        for row in rows:
            print(f"ID: {row['id']}")
            print(f"DE: {row['de']}")
            print(f"RU: {row['ru']}")
            print(f"Article: {row['article']}")
            print(f"Plural: {row['plural']}")
            print(f"Synonyms: {row['synonyms']}")
            print(f"Antonyms: {row['antonyms']}")
            print(f"Examples: {row['examples']}")
            print("-" * 20)
            
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_word()
