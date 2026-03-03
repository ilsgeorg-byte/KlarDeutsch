#!/usr/bin/env python3
"""
Исправить Rock обратно на юбка
"""

import os, sys, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))

import psycopg2

conn = psycopg2.connect(os.environ.get("POSTGRES_URL"))
cur = conn.cursor()

# Находим слово Rock
cur.execute("SELECT id, de, ru, article FROM words WHERE de ILIKE '%rock%' OR ru ILIKE '%юбка%'")
rows = cur.fetchall()

print("Найдены слова:\n")
for row in rows:
    print(f"  ID: {row[0]}, DE: {row[1]}, RU: {row[2]}, Article: {row[3]}")

# Исправляем
print("\nИсправление Rock = юбка...\n")
cur.execute("""
    UPDATE words SET 
        ru = 'юбка',
        article = 'der',
        ai_checked_at = NULL
    WHERE de = 'Rock'
""")

conn.commit()
cur.close()
conn.close()

print("✅ Исправлено!")
print("\nТеперь Rock = юбка (правильно)")
