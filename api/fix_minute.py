#!/usr/bin/env python3
"""
Исправить Zeitung = газета
"""

import os, sys, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))

import psycopg2

conn = psycopg2.connect(os.environ.get("POSTGRES_URL"))
cur = conn.cursor()

# Исправляем die Zeitung -> Zeitung
print("Исправление Zeitung...\n")
cur.execute("""
    UPDATE words SET
        de = 'Zeitung',
        ru = 'газета',
        article = 'die',
        plural = 'Zeitungen'
    WHERE de = 'die Zeitung'
""")
conn.commit()
print(f"Исправлено записей: {cur.rowcount}")

# Проверка
cur.execute("SELECT id, de, ru, article, plural FROM words WHERE de = 'Zeitung'")
row = cur.fetchone()
if row:
    print(f"\nТеперь: {row}")

cur.close()
conn.close()
print("\nГотово!")
