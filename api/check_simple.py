#!/usr/bin/env python3
"""
Простая AI проверка слов - без зависаний
"""

import os, sys, json, re
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))

import psycopg2
from openai import OpenAI

# Настройки
CHECK_LIMIT = 5
DRY_RUN = False

# Client
client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
    timeout=15
)

# DB
def get_db():
    url = os.environ.get("POSTGRES_URL")
    return psycopg2.connect(url)

# Промпт
PROMPT = """
Проверь немецкое слово строго.
Слово: {de} = {ru} (артикль: {article})
Верни JSON: {{"valid": true/false, "errors": [], "corrected_ru": ""}}
"""

print(f"AI Check - {CHECK_LIMIT} words\n")
print("=" * 50)

conn = get_db()
cur = conn.cursor()

# Берём слова
cur.execute("""
    SELECT id, de, ru, article 
    FROM words 
    ORDER BY ai_checked_at ASC NULLS FIRST 
    LIMIT %s
""", (CHECK_LIMIT,))

words = cur.fetchall()
print(f"Found: {len(words)} words\n")

for i, (word_id, de, ru, article) in enumerate(words, 1):
    print(f"[{i}/{len(words)}] {de} = {ru}...", end=" ")
    
    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": PROMPT.format(de=de, ru=ru, article=article or "-")}],
            temperature=0.1,
            max_tokens=300
        )
        
        content = resp.choices[0].message.content.strip()
        
        # Парсим JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        
        result = json.loads(content)
        
        if result.get('valid'):
            print("OK")
        else:
            print(f"ERRORS: {result.get('errors', [])}")
            if not DRY_RUN and result.get('corrected_ru'):
                cur.execute("UPDATE words SET ru = %s WHERE id = %s", (result['corrected_ru'], word_id))
                conn.commit()
                print(f"  -> Fixed: {ru} -> {result['corrected_ru']}")
        
        # Mark as checked
        cur.execute("UPDATE words SET ai_checked_at = NOW() WHERE id = %s", (word_id,))
        conn.commit()
        
    except Exception as e:
        print(f"ERR: {str(e)[:50]}")

cur.close()
conn.close()

print("\n" + "=" * 50)
print("Done!")
