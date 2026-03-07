#!/usr/bin/env python3
"""
Найти и удалить все тестовые слова из базы
"""

import os, sys, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))

import psycopg2

conn = psycopg2.connect(os.environ.get("POSTGRES_URL"))
cur = conn.cursor()

print("🔍 Поиск тестовых слов...\n")

# Паттерны для поиска тестовых слов
test_patterns = [
    "Test%",
    "test%",
    "%Test%",
    "%test%",
    "Тест%",
    "тест%",
    "%Тест%",
    "%тест%",
    "Wort%",  # Немецкие тестовые слова
    "wort%",
]

deleted_count = 0

for pattern in test_patterns:
    cur.execute("""
        SELECT id, de, ru, level 
        FROM words 
        WHERE de ILIKE %s OR ru ILIKE %s
    """, (pattern, pattern))
    
    words = cur.fetchall()
    
    if words:
        print(f"📝 Найдено по паттерну '{pattern}': {len(words)} слов")
        for word in words:
            print(f"   ID: {word[0]}, DE: {word[1]}, RU: {word[2]}, Level: {word[3]}")
            deleted_count += 1

print(f"\n⚠️  Всего найдено: {deleted_count} тестовых слов\n")

# Спрашиваем подтверждение
if deleted_count > 0:
    response = input("Удалить все найденные тестовые слова? (y/n): ")
    
    if response.lower() == 'y':
        print("\n🗑️  Удаление...\n")
        
        for pattern in test_patterns:
            cur.execute("""
                DELETE FROM user_words 
                WHERE word_id IN (
                    SELECT id FROM words 
                    WHERE de ILIKE %s OR ru ILIKE %s
                )
            """, (pattern, pattern))
            
            cur.execute("""
                DELETE FROM words 
                WHERE de ILIKE %s OR ru ILIKE %s
            """, (pattern, pattern))
            
            deleted = cur.rowcount
            if deleted > 0:
                print(f"   Удалено по паттерну '{pattern}': {deleted}")
        
        conn.commit()
        print("\n✅ Все тестовые слова удалены!")
    else:
        print("\n❌ Удаление отменено")
else:
    print("✅ Тестовых слов не найдено!")

cur.close()
conn.close()
