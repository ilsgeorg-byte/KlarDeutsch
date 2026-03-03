#!/usr/bin/env python3
"""
Исправить слова со смешением алфавитов
"""

import os, sys, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))

import psycopg2

conn = psycopg2.connect(os.environ.get("POSTGRES_URL"))
cur = conn.cursor()

# Слова для исправления
fixes = [
    # (de, correct_ru, correct_article)
    ("das Zeugnis", "Свидетельство", "das"),
    ("das Zeugnis", "Аттестат", "das"),
    ("die Entschuldigung", "Извинение", "die"),
]

print("Исправление слов со смешением алфавитов...\n")

for i, (de_search, correct_ru, correct_article) in enumerate(fixes, 1):
    # Находим слово по немецкому
    cur.execute("SELECT id, de, ru, article FROM words WHERE de ILIKE %s", (f'%{de_search.split()[1]}%',))
    rows = cur.fetchall()
    
    for row in rows:
        word_id, de, ru, article = row
        # Проверяем есть ли смесь алфавитов в переводе
        has_cyrillic = any('\u0400' <= c <= '\u04FF' for c in ru)
        has_latin = any('a' <= c.lower() <= 'z' for c in ru)
        
        if has_cyrillic and has_latin:
            print(f"[{i}] Найдено: {de} = {ru}")
            print(f"    Исправить на: {de} = {correct_ru} (артикль: {correct_article})")
            
            cur.execute("""
                UPDATE words SET ru = %s, article = %s, ai_checked_at = NULL
                WHERE id = %s
            """, (correct_ru, correct_article, word_id))
            print(f"    ✅ Исправлено!")

conn.commit()
cur.close()
conn.close()

print("\n✅ Готово!")
