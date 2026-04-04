import os
import psycopg2
from dotenv import load_dotenv

load_dotenv('.env.local')

POSTGRES_URL = os.getenv('POSTGRES_URL')

def inspect_first_batch():
    conn = psycopg2.connect(POSTGRES_URL)
    cur = conn.cursor()
    
    query = """
      SELECT id, de, ru, article, plural, verb_forms, ai_checked_at
      FROM words 
      WHERE 
        ai_checked_at IS NULL 
        OR (
          ai_checked_at < '2026-04-04' AND (
            (de ~* '^(der|die|das) ' AND (plural IS NULL OR plural = '' OR plural = '—' OR plural = '-')) OR
            ((article IS NULL OR article = '') AND (verb_forms IS NULL OR verb_forms = '' OR (LENGTH(verb_forms) - LENGTH(REPLACE(verb_forms, ',', ''))) < 3) AND de !~ ' ' AND length(de) > 2 AND length(ru) > 2)
          )
        )
      ORDER BY ai_checked_at NULLS FIRST, id
      LIMIT 10
    """
    
    cur.execute(query)
    rows = cur.fetchall()
    print("--- First 10 words in queue ---")
    for row in rows:
        print(row)
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    inspect_first_batch()
