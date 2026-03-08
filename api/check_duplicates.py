#!/usr/bin/env python3
"""
Проверить слова на дубликаты между уровнями
"""

import os, sys, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))

import psycopg2

conn = psycopg2.connect(os.environ.get("POSTGRES_URL"))
cur = conn.cursor()

print("🔍 Проверка на дубликаты между уровнями...\n")

# Находим дубликаты (одинаковые de+ru но разные уровни)
cur.execute("""
    SELECT w1.de, w1.ru, w1.level as level1, w2.level as level2, w1.id as id1, w2.id as id2
    FROM words w1
    JOIN words w2 ON w1.de = w2.de AND w1.ru = w2.ru AND w1.level != w2.level
    WHERE w1.id < w2.id
    ORDER BY w1.de, w1.ru
""")

duplicates = cur.fetchall()

if duplicates:
    print(f"⚠️  Найдено дубликатов: {len(duplicates)}\n")
    
    # Группируем по словам
    seen = set()
    for de, ru, level1, level2, id1, id2 in duplicates:
        key = f"{de}_{ru}"
        if key not in seen:
            print(f"📝 {de} = {ru}")
            print(f"   Уровень {level1} (ID: {id1})")
            print(f"   Уровень {level2} (ID: {id2})")
            print()
            seen.add(key)
    
    # Предлагаем удалить
    response = input("\nУдалить дубликаты (оставить только один экземпляр)? (y/n): ")
    
    if response.lower() == 'y':
        print("\n🗑️  Удаление дубликатов...\n")
        
        deleted_count = 0
        for de, ru, level1, level2, id1, id2 in duplicates:
            key = f"{de}_{ru}"
            if key in seen:
                # Удаляем вторую копию (с большим ID)
                cur.execute("DELETE FROM user_words WHERE word_id = %s", (id2,))
                cur.execute("DELETE FROM words WHERE id = %s", (id2,))
                print(f"   ❌ Удалено: {de} = {ru} (уровень {level2}, ID: {id2})")
                deleted_count += 1
                seen.remove(key)
        
        conn.commit()
        print(f"\n✅ Удалено {deleted_count} дубликатов!")
else:
    print("✅ Дубликатов не найдено!")

# Проверка на одинаковые слова внутри одного уровня
print("\n\n🔍 Проверка дубликатов внутри уровней...\n")

cur.execute("""
    SELECT de, ru, level, COUNT(*) as count
    FROM words
    GROUP BY de, ru, level
    HAVING COUNT(*) > 1
    ORDER BY de, ru
""")

internal_dups = cur.fetchall()

if internal_dups:
    print(f"⚠️  Найдено внутренних дубликатов: {len(internal_dups)}\n")
    for de, ru, level, count in internal_dups:
        print(f"📝 {de} = {ru} (уровень {level}) - повторяется {count} раз")
else:
    print("✅ Внутренних дубликатов не найдено!")

cur.close()
conn.close()
