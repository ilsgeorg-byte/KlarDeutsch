#!/usr/bin/env python3
"""
Исправить примеры использования для Schinken
"""

import os, sys, io, json
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))

import psycopg2

conn = psycopg2.connect(os.environ.get("POSTGRES_URL"))
cur = conn.cursor()

print("Исправление примеров Schinken...\n")

# Новые правильные примеры
examples = [
    {
        "de": "Ich esse gerne Schinken zum Frühstück.",
        "ru": "Я люблю есть ветчину на завтрак."
    },
    {
        "de": "Der Schinken ist sehr lecker.",
        "ru": "Ветчина очень вкусная."
    },
    {
        "de": "Ich kaufe einen Schinken für den Grill.",
        "ru": "Я покупаю ветчину для гриля."
    }
]

# Исправляем примеры в JSONB колонке examples
cur.execute("""
    UPDATE words SET 
        examples = %s::jsonb,
        example_de = %s,
        example_ru = %s,
        ai_checked_at = NULL
    WHERE de = 'Schinken'
""", (
    json.dumps(examples, ensure_ascii=False),
    examples[0]["de"],
    examples[0]["ru"]
))

updated = cur.rowcount
print(f"Исправлено слов: {updated}")

# Проверяем что получилось
cur.execute("SELECT de, ru, examples FROM words WHERE de = 'Schinken'")
row = cur.fetchone()
if row and row[2]:
    print(f"\n✅ Примеры:")
    for ex in row[2]:
        print(f"   DE: {ex['de']}")
        print(f"   RU: {ex['ru']}")
        print()

conn.commit()
cur.close()
conn.close()

print("✅ Готово!")
