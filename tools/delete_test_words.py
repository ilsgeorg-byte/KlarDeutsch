#!/usr/bin/env python3
"""
Удалить только явные тестовые слова
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

    print("🗑️  Удаление явных тестовых слов...\n")

    # Только явные тестовые слова
    test_word_ids = [6031, 6032, 6033]  # Testwort, TestWort2, TestWort3

    deleted_count = 0

    for word_id in test_word_ids:
        cur.execute("SELECT de, ru FROM words WHERE id = %s", (word_id,))
        word = cur.fetchone()

        if word:
            # Сначала удаляем из user_words
            cur.execute("DELETE FROM user_words WHERE word_id = %s", (word_id,))

            # Потом из words
            cur.execute("DELETE FROM words WHERE id = %s", (word_id,))

            print(f"   ❌ Удалено: {word[0]} = {word[1]}")
            deleted_count += 1

    conn.commit()

    print(f"\n✅ Удалено {deleted_count} тестовых слов!")

except Exception as e:
    print(f"❌ Ошибка: {e}")
    if conn:
        conn.rollback()
finally:
    if cur:
        cur.close()
    if conn:
        conn.close()
