#!/usr/bin/env python3
"""
Исправить ошибку перевода Schinken
"""

import os, sys, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))

import psycopg2

conn = psycopg2.connect(os.environ.get("POSTGRES_URL"))
cur = conn.cursor()

print("Исправление Schinken...\n")

# Исправляем перевод и немецкое слово (убираем артикль из de)
cur.execute("""
    UPDATE words SET 
        de = 'Schinken',
        ru = 'Ветчина',
        article = 'der',
        ai_checked_at = NULL
    WHERE id = 3409
""")

updated = cur.rowcount
print(f"Исправлено слов: {updated}")

# Проверяем что получилось
cur.execute("SELECT de, ru, article FROM words WHERE id = 3409")
row = cur.fetchone()
if row:
    print(f"\n✅ Теперь: {row[0]} = {row[1]} (артикль: {row[2]})")

conn.commit()
cur.close()
conn.close()

print("\n✅ Готово!")
