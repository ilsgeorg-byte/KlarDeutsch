#!/usr/bin/env python3
"""
Скрипт для исправления ошибки в слове "Zeitung"
- Правильный перевод: "газета" (а не "Немецкая газета")
- Множественное число: "Zeitungen" (газеты)
"""

import os
import sys
import io
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))

import psycopg2

def get_db_connection():
    url = os.environ.get("POSTGRES_URL")
    if not url:
        raise Exception("POSTGRES_URL не найдена")
    return psycopg2.connect(url)

def fix_zeitung():
    """Исправляет ошибку в слове Zeitung"""
    print("Исправление ошибки в слове 'Zeitung'...")

    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Проверяем текущую запись
        cur.execute("""
            SELECT id, de, ru, article, plural FROM words 
            WHERE LOWER(de) = 'zeitung'
        """)
        row = cur.fetchone()
        
        if row:
            print(f"Найдено: id={row[0]}, de='{row[1]}', ru='{row[2]}', article='{row[3]}', plural='{row[4]}'")
        
        # Исправляем перевод и добавляем множественное число
        cur.execute("""
            UPDATE words
            SET ru = 'газета',
                plural = 'Zeitungen'
            WHERE LOWER(de) = 'zeitung'
        """)
        
        rows_affected = cur.rowcount
        conn.commit()
        
        if rows_affected > 0:
            print(f"\nИсправлено {rows_affected} запись(ей)")
            print("Теперь 'Zeitung' = 'газета' (а не 'Немецкая газета')")
            print("Множественное число: 'Zeitungen'")
        else:
            print("Запись не найдена или не требует исправления")
            
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Ошибка: {e}")
        raise
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def main():
    print("=" * 60)
    print("ИСПРАВЛЕНИЕ: Zeitung")
    print("=" * 60)
    print()
    print("Текущая ошибка:")
    print("  Zeitung = 'Немецкая газета' ❌")
    print()
    print("Будет исправлено на:")
    print("  Zeitung = 'газета' ✓")
    print("  Множественное число: 'Zeitungen' ✓")
    print()

    response = input("Исправить? (введите 'ДА' для подтверждения): ")

    if response.strip().upper() == 'ДА':
        fix_zeitung()
        print("\nГотово!")
    else:
        print("\nОтменено.")

if __name__ == "__main__":
    main()
