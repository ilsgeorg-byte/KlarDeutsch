#!/usr/bin/env python3
"""
Исправить прилагательные обратно (ИИ ошибся)
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

    # Прилагательные НЕ ИМЕЮТ артикля!
    adjectives = [
        ("kurz", "короткий"),
        ("leicht", "легкий"),
        ("schwer", "тяжелый"),
    ]

    # Месяцы и времена года имеют артикль DER
    months_seasons = [
        ("Mai", "май", "der"),
        ("Juni", "июнь", "der"),
        ("Frühling", "весна", "der"),
    ]

    print("Исправление прилагательных...\n")

    for de, ru in adjectives:
        cur.execute("""
            UPDATE words SET article = '', ai_checked_at = NULL
            WHERE de = %s AND ru = %s
        """, (de, ru))
        print(f"  ✅ {de} = {ru} (прилагательное, без артикля)")

    print("\nИсправление месяцев/времён года...\n")

    for de, ru, article in months_seasons:
        cur.execute("""
            UPDATE words SET article = %s, ai_checked_at = NULL
            WHERE de = %s AND ru = %s
        """, (article, de, ru))
        print(f"  ✅ {article} {de} = {ru}")

    # Удалим пустые слова (сначала user_words, потом words)
    print("\nУдаление пустых слов...")
    try:
        cur.execute("DELETE FROM user_words WHERE word_id IN (SELECT id FROM words WHERE de = '' OR de IS NULL OR ru = '' OR ru IS NULL)")
        cur.execute("DELETE FROM words WHERE de = '' OR de IS NULL OR ru = '' OR ru IS NULL")
        deleted = cur.rowcount
        print(f"  Удалено: {deleted}")
    except Exception as e:
        print(f"  ⚠️  Не удалось удалить: {e}")

    conn.commit()
    print("\n✅ Исправлено!")

except Exception as e:
    print(f"❌ Ошибка: {e}")
    if conn:
        conn.rollback()
finally:
    if cur:
        cur.close()
    if conn:
        conn.close()
