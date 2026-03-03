#!/usr/bin/env python3
"""
Ручное исправление конкретных слов в БД
"""

import os
import sys
import io
from dotenv import load_dotenv

# Фикс для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))

import psycopg2

def get_db_connection():
    url = os.environ.get("POSTGRES_URL")
    if not url:
        raise Exception("POSTGRES_URL не найдена")
    return psycopg2.connect(url)

def main():
    print("Исправление слов вручную...\n")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Список слов для исправления
    fixes = [
        # (de, correct_ru, correct_article)
        ("Entschuldigung", "Извинение", "die"),
        ("die Entschuldigung", "Извинение", "die"),
    ]
    
    for de, correct_ru, correct_article in fixes:
        # Проверяем есть ли такое слово
        cur.execute("SELECT id, de, ru, article FROM words WHERE de = %s OR de = %s", (de, de))
        row = cur.fetchone()
        
        if row:
            word_id, current_de, current_ru, current_article = row
            print(f"Найдено: {current_de} = {current_ru} (артикль: {current_article})")
            print(f"Исправить на: {current_de} = {correct_ru} (артикль: {correct_article})")
            
            # Исправляем
            cur.execute("""
                UPDATE words SET ru = %s, article = %s
                WHERE id = %s
            """, (correct_ru, correct_article, word_id))
            conn.commit()
            
            print(f"✅ Исправлено!\n")
        else:
            print(f"❌ Не найдено: {de}\n")
    
    cur.close()
    conn.close()
    
    print("Готово!")

if __name__ == "__main__":
    main()
