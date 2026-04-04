#!/usr/bin/env python3
"""
Проверка слов без plural и verb_forms - показывает статистику
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

def main():
    print("=" * 60)
    print("Статистика отсутствующих форм в базе данных")
    print("=" * 60)
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Общее количество слов
    cur.execute("SELECT COUNT(*) FROM words")
    total_words = cur.fetchone()[0]
    print(f"\nВсего слов: {total_words}")
    
    # Слова без plural (существительные с артиклем)
    cur.execute("""
        SELECT COUNT(*)
        FROM words
        WHERE article IS NOT NULL AND article != ''
          AND (plural IS NULL OR plural = '')
    """)
    nouns_without_plural = cur.fetchone()[0]
    print(f"Существительных без plural: {nouns_without_plural}")
    
    # Слова без verb_forms (без артикля)
    cur.execute("""
        SELECT COUNT(*)
        FROM words
        WHERE (article IS NULL OR article = '')
          AND (verb_forms IS NULL OR verb_forms = '')
    """)
    words_without_verb_forms = cur.fetchone()[0]
    print(f"Слов без verb_forms (глаголы + прилагательные): {words_without_verb_forms}")
    
    # Примеры существительных без plural
    print(f"\nПримеры существительных без plural (первые 15):")
    cur.execute("""
        SELECT id, article, de, ru, plural
        FROM words
        WHERE article IS NOT NULL AND article != ''
          AND (plural IS NULL OR plural = '')
        ORDER BY id
        LIMIT 15
    """)
    for row in cur.fetchall():
        print(f"  ID {row[0]}: {row[1]} {row[2]} = {row[3]} (plural: {row[4] or 'отсутствует'})")
    
    # Примеры слов без verb_forms (смешанные)
    print(f"\nПримеры слов без verb_forms (первые 15, AI определит тип):")
    cur.execute("""
        SELECT id, de, ru, article, verb_forms
        FROM words
        WHERE (article IS NULL OR article = '')
          AND (verb_forms IS NULL OR verb_forms = '')
        ORDER BY id
        LIMIT 15
    """)
    for row in cur.fetchall():
        print(f"  ID {row[0]}: {row[1]} = {row[2]} (article: {row[3] or 'нет'}, verb_forms: {row[4] or 'отсутствует'})")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("Для умного заполнения запусти: python tools/smart_fill_missing_forms.py")
    print("AI сам определит тип слова и заполнит нужные поля")
    print("=" * 60)

if __name__ == "__main__":
    main()
