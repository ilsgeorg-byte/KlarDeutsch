#!/usr/bin/env python3
"""
Исправить ошибки ИИ (прилагательные, глаголы, месяцы)
"""

import os, sys, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))

import psycopg2

conn = psycopg2.connect(os.environ.get("POSTGRES_URL"))
cur = conn.cursor()

# Прилагательные — БЕЗ артикля
adjectives = [
    ("leicht", "легкий"),
    ("schwer", "тяжелый"),
]

# Месяцы/времена года — DER
months_seasons = [
    ("Mai", "май", "der"),
    ("Juni", "июнь", "der"),
    ("Frühling", "весна", "der"),
]

# Глаголы — правильные формы
verbs = {
    "wohnen": ("проживать", "wohnen, wohnte, hat gewohnt"),
    "anprobieren": ("попробовать", "anprobieren, probierte an, hat angeprobt"),
    "anziehen": ("одеться", "anziehen, zog an, hat angezogen"),
    "buchen": ("бронировать", "buchen, buchte, hat gebucht"),
    "einkaufen": ("покупать", "einkaufen, kaufte ein, hat eingekauft"),
    "einladen": ("приглашать", "einladen, lud ein, hat eingeladen"),
}

print("Исправление прилагательных...\n")
for de, ru in adjectives:
    cur.execute("UPDATE words SET article = '', verb_forms = '', ai_checked_at = NULL WHERE de = %s AND ru = %s", (de, ru))
    print(f"  ✅ {de} = {ru} (прилагательное)")

print("\nИсправление месяцев/времён года...\n")
for de, ru, article in months_seasons:
    cur.execute("UPDATE words SET article = %s, ai_checked_at = NULL WHERE de = %s AND ru = %s", (article, de, ru))
    print(f"  ✅ {article} {de} = {ru}")

print("\nИсправление глаголов...\n")
for de, (ru, verb_forms) in verbs.items():
    cur.execute("""
        UPDATE words SET 
            ru = %s, 
            verb_forms = %s,
            article = '',
            ai_checked_at = NULL
        WHERE de = %s
    """, (ru, verb_forms, de))
    print(f"  ✅ {de} = {ru} ({verb_forms})")

conn.commit()
cur.close()
conn.close()

print("\n✅ Исправлено!")
