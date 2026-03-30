
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
    
    # Ищем все слова
    cur.execute("SELECT id, de, article FROM words")
    rows = cur.fetchall()
    
    found = 0
    for row in rows:
        old_de = row['de']
        if not old_de: continue
        
        # Проверяем "die die ", "der der ", "das das "
        # Также проверяем "die  die " (два пробела)
        match = re.search(r'^(der|die|das)\s+(der|die|das)\s+(.*)', old_de, flags=re.IGNORECASE)
        if match:
            art1 = match.group(1)
            art2 = match.group(2)
            word = match.group(3)
            
            if art1.lower() == art2.lower():
                new_de = f"{art1} {word}"
                print(f"ID: {row['id']}, DE: {old_de} -> {new_de}")
                cur.execute("UPDATE words SET de = %s WHERE id = %s", (new_de, row['id']))
                found += 1

    if found > 0:
        print(f"Fixed {found} double articles.")
    else:
        print("No double articles found.")

    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    fix_double_articles()
