#!/usr/bin/env python3
"""
Скрипт для сброса статуса AI проверки у всех слов в базе данных
После запуска этого скрипта все слова будут помечены как "непроверенные"
и проверка начнется с начала
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

def reset_ai_check_status():
    """Сбрасывает статус AI проверки для всех слов"""
    print("Сброс статуса AI проверки для всех слов...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Сбрасываем поле ai_checked_at для всех слов
    cur.execute("""
        UPDATE words 
        SET ai_checked_at = NULL
    """)
    
    rows_affected = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"Статус проверки сброшен для {rows_affected} слов")
    print("Теперь при следующем запуске проверка начнется с начала")

def main():
    print("=" * 60)
    print("СБРОС СТАТУСА AI ПРОВЕРКИ")
    print("=" * 60)
    
    print(f"Внимание! Это действие сбросит статус проверки для ВСЕХ слов в базе данных.")
    print(f"После этого проверка будет начинаться с начала.")
    print()
    
    response = input("Вы уверены, что хотите продолжить? (введите 'ДА' для подтверждения): ")
    
    if response.strip().upper() == 'ДА':
        reset_ai_check_status()
        print("\nСброс завершен успешно!")
    else:
        print("\nОперация отменена.")

if __name__ == "__main__":
    main()