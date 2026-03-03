#!/usr/bin/env python3
"""
Сбросить ai_checked_at только для слов с ошибками (Freund, Montag и т.д.)
"""

import os, sys
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))

import psycopg2

conn = psycopg2.connect(os.environ.get("POSTGRES_URL"))
cur = conn.cursor()

print("Сброс для слов с mixed alphabet...")

# Находим слова которые были помечены как проверенные но имели "Смешение алфавитов"
# Это слова где ru содержит кириллицу, de содержит латиницу (правильные слова)
cur.execute("""
    UPDATE words 
    SET ai_checked_at = NULL 
    WHERE ai_checked_at IS NOT NULL
    AND (
        -- Немецкое слово содержит только латиницу (это правильно)
        de ~ '^[A-Za-zÄÖÜäöüß\s-]+$'
        AND
        -- Перевод содержит только кириллицу (это правильно)
        ru ~ '^[А-Яа-яЁё\s-]+$'
    )
""")

updated = cur.rowcount
conn.commit()
cur.close()
conn.close()

print(f"Сброшено: {updated} слов (правильные слова)")
print("\nТеперь можно запустить проверку заново:")
print("  python check_words_ai.py")
