#!/usr/bin/env python3
"""
Шаг 1: Получить слова из БД для проверки
Сохраняет в words_to_check.json
"""

import os, sys, json
if sys.platform == 'win32':
    sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))

import psycopg2

# Настройки
CHECK_LIMIT = 10  # Сколько слов получить

def get_db():
    url = os.environ.get("POSTGRES_URL")
    return psycopg2.connect(url)

print(f"Getting {CHECK_LIMIT} words from DB...\n")

conn = get_db()
cur = conn.cursor()

# Берём непроверенные или старые слова
cur.execute("""
    SELECT id, de, ru, article, verb_forms, example_de, example_ru
    FROM words 
    ORDER BY ai_checked_at ASC NULLS FIRST 
    LIMIT %s
""", (CHECK_LIMIT,))

words = []
for row in cur.fetchall():
    words.append({
        'id': row[0],
        'de': row[1],
        'ru': row[2],
        'article': row[3],
        'verb_forms': row[4],
        'example_de': row[5],
        'example_ru': row[6]
    })

cur.close()
conn.close()

# Сохраняем в JSON
with open('words_to_check.json', 'w', encoding='utf-8') as f:
    json.dump(words, f, ensure_ascii=False, indent=2)

print(f"✅ Saved {len(words)} words to words_to_check.json")
print("\nFirst 3 words:")
for w in words[:3]:
    print(f"  {w['de']} = {w['ru']}")
