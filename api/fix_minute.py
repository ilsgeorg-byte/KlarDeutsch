#!/usr/bin/env python3
"""
Исправить Minute обратно (ИИ ошибся)
"""

import os, sys, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))

import psycopg2

conn = psycopg2.connect(os.environ.get("POSTGRES_URL"))
cur = conn.cursor()

# Исправляем Minute
print("Исправление Minute = минута...\n")
cur.execute("""
    UPDATE words SET 
        ru = 'минута',
        article = 'die',
        ai_checked_at = NULL
    WHERE de = 'Minute'
""")

conn.commit()
cur.close()
conn.close()

print("✅ Исправлено!")
print("\nТеперь: die Minute = минута (правильно)")
