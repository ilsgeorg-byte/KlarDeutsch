#!/usr/bin/env python3
"""
Сбросить счётчик проверок (ai_checked_at = NULL)
"""

import os, sys
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))

import psycopg2

url = os.environ.get("POSTGRES_URL")
if not url:
    print("POSTGRES_URL не найдена")
    sys.exit(1)

conn = None
cur = None
try:
    conn = psycopg2.connect(url)
    cur = conn.cursor()

    print("Сброс ai_checked_at...")

    cur.execute("UPDATE words SET ai_checked_at = NULL")
    updated = cur.rowcount

    conn.commit()
    print(f"Готово! Сброшено: {updated} слов")
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
