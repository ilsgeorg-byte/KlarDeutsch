#!/usr/bin/env python3
"""
Скрипт для исправления ошибок в словах, таких как:
- Неправильные формы глагола у существительных
- Неправильные переводы
- Неправильные артикли
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

def fix_problematic_words():
    """Исправляет известные ошибки в словах"""
    print("Исправление известных ошибок в словах...")

    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Исправление ошибки с "Guten Morgen" - это не глагол, а существительное/выражение
        # Убираем формы глагола и добавляем правильный артикль если нужно
        cur.execute("""
            UPDATE words
            SET verb_forms = '',
                article = CASE WHEN article = '' OR article IS NULL THEN 'der' ELSE article END
            WHERE LOWER(de) = 'guten morgen' OR LOWER(de) LIKE '%guten morgen%'
        """)

        # Исправление других возможных ошибок
        # Убираем формы глагола у существительных, которые их не должны иметь
        cur.execute("""
            UPDATE words
            SET verb_forms = ''
            WHERE (article = 'der' OR article = 'die' OR article = 'das')
            AND verb_forms != ''
            AND (LOWER(de) LIKE '%tag%' OR LOWER(de) LIKE '%nacht%' OR LOWER(de) LIKE '%morgen%'
                 OR LOWER(de) LIKE '%abend%' OR LOWER(de) LIKE '%frau%' OR LOWER(de) LIKE '%mann%'
                 OR LOWER(de) LIKE '%haus%' OR LOWER(de) LIKE '%kind%' OR LOWER(de) LIKE '%frau%'
                 OR LOWER(de) LIKE '%stadt%' OR LOWER(de) LIKE '%land%' OR LOWER(de) LIKE '%welt%')
        """)

        # Убираем артикли у глаголов, которые их не должны иметь
        cur.execute("""
            UPDATE words
            SET article = ''
            WHERE verb_forms != ''
            AND (article = 'der' OR article = 'die' OR article = 'das')
            AND (LOWER(de) LIKE '%en$' OR LOWER(de) LIKE '%n$' OR LOWER(de) LIKE '%ln$'
                 OR LOWER(de) LIKE '%rn$' OR LOWER(de) LIKE '%en ' OR LOWER(de) LIKE '%n '
                 OR de ILIKE 'zu %' OR de ILIKE 'sich %' OR de ILIKE 'sein %')
        """)

        rows_affected = cur.rowcount
        conn.commit()
        print(f"Исправлено {rows_affected} записей в базе данных")
        print("Ошибки в словах успешно исправлены")
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
    print("ИСПРАВЛЕНИЕ ОШИБОК В СЛОВАХ")
    print("=" * 60)
    
    print(f"Исправление ошибок в данных слов:")
    print(f"- Неправильные формы глагола у существительных")
    print(f"- Неправильные артикли у глаголов")
    print(f"- Пример: 'Guten Morgen' с формой 'kritisieren, kritisierte, kritisiert'")
    print()
    
    response = input("Вы уверены, что хотите продолжить? (введите 'ДА' для подтверждения): ")
    
    if response.strip().upper() == 'ДА':
        fix_problematic_words()
        print("\nИсправление завершено успешно!")
    else:
        print("\nОперация отменена.")

if __name__ == "__main__":
    main()