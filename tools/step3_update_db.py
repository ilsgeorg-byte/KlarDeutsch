#!/usr/bin/env python3
"""
Шаг 3: Обновить БД с результатами
Читает results.json, обновляет words
"""

import os, sys, json
if sys.platform == 'win32':
    sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))

import psycopg2

# Настройки
DRY_RUN = False  # True = только просмотр, False = исправлять

def get_db():
    url = os.environ.get("POSTGRES_URL")
    return psycopg2.connect(url)

print("Update DB from results.json\n")
print("=" * 50)

if DRY_RUN:
    print("⚠️  DRY RUN - No changes to DB\n")

# Читаем результаты
with open('results.json', 'r', encoding='utf-8') as f:
    results = json.load(f)

print(f"Processing {len(results)} results...\n")

conn = None
cur = None
try:
    conn = get_db()
    cur = conn.cursor()

    updated = 0
    for r in results:
        if 'error' in r:
            continue  # Пропускаем ошибки

        if r.get('valid'):
            # Слово верное - просто отмечаем как проверенное
            if not DRY_RUN:
                cur.execute("UPDATE words SET ai_checked_at = NOW() WHERE id = %s", (r['id'],))
            updated += 1
        else:
            # Есть ошибки - исправляем
            word_id = r['id']

            if not DRY_RUN:
                # Преобразуем verb_forms из dict в строку
                vf = r.get('corrected_verb_forms')
                if isinstance(vf, dict):
                    vf = f"{vf.get('Infinitiv', '')}, {vf.get('Präteritum', '')}, {vf.get('Partizip II', '')}"

                cur.execute("""
                    UPDATE words SET
                        de = %s,
                        ru = %s,
                        article = %s,
                        verb_forms = %s,
                        example_de = %s,
                        example_ru = %s,
                        ai_checked_at = NOW()
                    WHERE id = %s
                """, (
                    r.get('corrected_de'),
                    r.get('corrected_ru'),
                    r.get('corrected_article') or None,
                    vf,
                    r.get('corrected_example_de') or None,
                    r.get('corrected_example_ru') or None,
                    word_id
                ))

            print(f"Fix word {word_id}: {r.get('errors', [])}")
            updated += 1

    if not DRY_RUN:
        conn.commit()

    print("\n" + "=" * 50)
    print(f"✅ Updated {updated} words")
    if DRY_RUN:
        print("⚠️  DRY RUN - Set DRY_RUN=False to apply changes")

except Exception as e:
    print(f"❌ Ошибка: {e}")
    if conn:
        conn.rollback()
finally:
    if cur:
        cur.close()
    if conn:
        conn.close()
