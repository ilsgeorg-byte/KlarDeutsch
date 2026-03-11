#!/usr/bin/env python3
"""
Добавляет колонку ai_checked_at для отслеживания проверенных слов
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))

import psycopg2

def get_db_connection():
    url = os.environ.get("POSTGRES_URL")
    if not url:
        raise Exception("POSTGRES_URL не найдена")
    return psycopg2.connect(url)

def main():
    print("Добавление колонки ai_checked_at...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Добавляем колонку
    try:
        cur.execute("""
            ALTER TABLE words 
            ADD COLUMN IF NOT EXISTS ai_checked_at TIMESTAMP DEFAULT NULL
        """)
        conn.commit()
        print("✅ Колонка ai_checked_at добавлена")
    except Exception as e:
        print(f"Ошибка: {e}")
        conn.rollback()
    
    # Индекс для быстрого поиска непроверенных слов
    try:
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_words_ai_checked 
            ON words (ai_checked_at)
            WHERE ai_checked_at IS NULL
        """)
        conn.commit()
        print("✅ Индекс создан")
    except Exception as e:
        print(f"Ошибка индекса: {e}")
        conn.rollback()
    
    cur.close()
    conn.close()
    
    print("\nГотово! Теперь скрипт будет проверять только непроверенные слова.")

if __name__ == "__main__":
    main()
