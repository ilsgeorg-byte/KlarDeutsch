#!/usr/bin/env python3
"""
Исправить испорченные слова (Kritisch -> оригинал)
"""

import os, sys, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))

import psycopg2

conn = None
cur = None
try:
    conn = psycopg2.connect(os.environ.get("POSTGRES_URL"))
    cur = conn.cursor()

    # Исправляем испорченные слова
    fixes = [
        (1, "Hallo", "Привет"),
        (2, "Guten Morgen", "Доброе утро"),
        (4, "Guten Tag", "Добрый день"),
    ]

    print("Исправление испорченных слов...\n")

    for word_id, de, ru in fixes:
        cur.execute("UPDATE words SET de = %s, ru = %s, ai_checked_at = NULL WHERE id = %s", (de, ru, word_id))
        print(f"  [{word_id}] {de} = {ru}")

    conn.commit()
    print("\n✅ Исправлено!")
    print("\nТеперь можно запустить проверку заново:")
    print("  python check_words_ai.py")

except Exception as e:
    print(f"❌ Ошибка: {e}")
    if conn:
        conn.rollback()
finally:
    if cur:
        cur.close()
    if conn:
        conn.close()
