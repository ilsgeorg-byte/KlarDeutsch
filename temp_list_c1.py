
import os, sys, json
import psycopg2
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env.local'))

def get_c1_words():
    conn = psycopg2.connect(os.environ.get("POSTGRES_URL"))
    cur = conn.cursor()
    cur.execute("""
        SELECT id, de, ru, level, article, verb_forms, plural, example_de, example_ru, synonyms, antonyms, collocations
        FROM words 
        WHERE level = 'C1' AND ai_checked_at IS NULL
        LIMIT 10
    """)
    words = []
    for row in cur.fetchall():
        words.append({
            'id': row[0],
            'de': row[1],
            'ru': row[2],
            'level': row[3],
            'article': row[4],
            'verb_forms': row[5],
            'plural': row[6],
            'example_de': row[7],
            'example_ru': row[8],
            'synonyms': row[9],
            'antonyms': row[10],
            'collocations': row[11]
        })
    cur.close()
    conn.close()
    return words

words = get_c1_words()
print(json.dumps(words, ensure_ascii=False, indent=2))
