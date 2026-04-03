
import os, sys, psycopg2, json
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env.local'))

def inspect():
    conn = psycopg2.connect(os.environ.get("POSTGRES_URL"))
    cur = conn.cursor()
    
    # Ищем последние 100 проверенных слов, у которых есть непустой plural
    cur.execute("""
        SELECT de, ru, plural, level, verb_forms
        FROM words 
        WHERE ai_checked_at IS NOT NULL AND plural IS NOT NULL AND plural != ''
        ORDER BY ai_checked_at DESC 
        LIMIT 100
    """)
    
    rows = cur.fetchall()
    print(f"--- Найдено {len(rows)} слов с множественным числом из последних проверок ---")
    for de, ru, plural, level, verb_forms in rows:
        tag = "[VERB! ERROR]" if verb_forms and (verb_forms != '') else ""
        print(f"{de} ({level}): {plural} {tag}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    inspect()
