#!/usr/bin/env python3
"""
Скрипт для поиска существительных без форм множественного числа
"""

import os
import sys
import io
from dotenv import load_dotenv

# Фикс для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Загружаем переменные окружения
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))

import psycopg2

def get_db_connection():
    url = os.environ.get("POSTGRES_URL")
    if not url:
        raise Exception("POSTGRES_URL не найдена")
    return psycopg2.connect(url)

def find_nouns_without_plural():
    """Находит существительные без форм множественного числа"""
    print("Поиск существительных без форм множественного числа...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Находим существительные (те, у которых есть артикль) без форм множественного числа
    cur.execute("""
        SELECT id, de, ru, article, plural
        FROM words
        WHERE article IS NOT NULL AND article != ''
          AND (plural IS NULL OR plural = '')
          AND (verb_forms IS NULL OR verb_forms = '')
        ORDER BY de
        LIMIT 4000
    """)
    
    nouns = cur.fetchall()
    
    print(f"Найдено {len(nouns)} существительных без форм множественного числа:")
    print("-" * 80)
    
    for row in nouns:
        word_id, de, ru, article, plural = row
        print(f"ID: {word_id} | {article} {de} = {ru} | Plural: {plural or 'отсутствует'}")
    
    cur.close()
    conn.close()

def main():
    print("=" * 80)
    print("ПОИСК СУЩЕСТВИТЕЛЬНЫХ БЕЗ ФОРМ МНОЖЕСТВЕННОГО ЧИСЛА")
    print("=" * 80)
    
    find_nouns_without_plural()
    print("\nДля исправления используйте скрипт check_noun_plural.py")

if __name__ == "__main__":
    main()