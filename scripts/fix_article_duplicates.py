#!/usr/bin/env python3
"""
Скрипт для исправления дублирующихся артиклей в базе данных
Находит и исправляет слова типа "die die Wohnung" → "die Wohnung"
"""

import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv('.env.local')

# Импортируем psycopg2
try:
    import psycopg2
except ImportError:
    print("Установите psycopg2: pip install psycopg2-binary")
    sys.exit(1)


def get_db_connection():
    """Подключение к базе данных"""
    url = os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL")
    
    if not url:
        print("❌ POSTGRES_URL не найдена в .env.local")
        sys.exit(1)
    
    try:
        conn = psycopg2.connect(url)
        print("✅ Подключение к базе данных успешно")
        return conn
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        sys.exit(1)


def fix_duplicates():
    """Исправление дублирующихся артиклей"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("\n🔍 Поиск проблемных записей...\n")
    
    # Находим все дублирующиеся артикли
    cur.execute("""
        SELECT id, article, de, ru 
        FROM words 
        WHERE article LIKE '% %'
           OR article LIKE 'die die%'
           OR article LIKE 'der der%'
           OR article LIKE 'das das%'
        LIMIT 20
    """)
    
    problematic = cur.fetchall()
    
    if problematic:
        print(f"Найдено {len(problematic)} записей с дублирующимися артиклями:\n")
        for row in problematic:
            print(f"  ID: {row[0]}, Артикль: '{row[1]}', Слово: {row[2]} ({row[3]})")
    else:
        print("✅ Проблемные записи не найдены")
    
    print("\n" + "="*60)
    print("ИСПРАВЛЕНИЕ")
    print("="*60 + "\n")
    
    # Исправляем "die die" → "die"
    cur.execute("""
        UPDATE words 
        SET article = TRIM(REPLACE(article, 'die die', 'die'))
        WHERE article LIKE '%die die%'
    """)
    fixed_die = cur.rowcount
    conn.commit()
    print(f"✅ Исправлено 'die die' → 'die': {fixed_die} записей")
    
    # Исправляем "der der" → "der"
    cur.execute("""
        UPDATE words 
        SET article = TRIM(REPLACE(article, 'der der', 'der'))
        WHERE article LIKE '%der der%'
    """)
    fixed_der = cur.rowcount
    conn.commit()
    print(f"✅ Исправлено 'der der' → 'der': {fixed_der} записей")
    
    # Исправляем "das das" → "das"
    cur.execute("""
        UPDATE words 
        SET article = TRIM(REPLACE(article, 'das das', 'das'))
        WHERE article LIKE '%das das%'
    """)
    fixed_das = cur.rowcount
    conn.commit()
    print(f"✅ Исправлено 'das das' → 'das': {fixed_das} записей")
    
    # Исправляем артикли с пробелами в начале/конце
    cur.execute("""
        UPDATE words 
        SET article = TRIM(article)
        WHERE article IS NOT NULL AND article != TRIM(article)
    """)
    fixed_trim = cur.rowcount
    conn.commit()
    print(f"✅ Удалены лишние пробелы: {fixed_trim} записей")
    
    print("\n" + "="*60)
    print("ПРОВЕРКА РЕЗУЛЬТАТА")
    print("="*60 + "\n")
    
    # Проверяем результат
    cur.execute("""
        SELECT id, article, de, ru 
        FROM words 
        WHERE article LIKE '% %'
           OR article LIKE 'die die%'
           OR article LIKE 'der der%'
           OR article LIKE 'das das%'
        LIMIT 10
    """)
    
    remaining = cur.fetchall()
    
    if remaining:
        print(f"⚠️  Осталось {len(remaining)} проблемных записей:\n")
        for row in remaining:
            print(f"  ID: {row[0]}, Артикль: '{row[1]}', Слово: {row[2]} ({row[3]})")
    else:
        print("✅ Все дублирующиеся артикли исправлены!")
    
    # Показываем пример исправленных слов
    print("\n" + "="*60)
    print("ПРИМЕРЫ ИСПРАВЛЕННЫХ СЛОВ")
    print("="*60 + "\n")
    
    cur.execute("""
        SELECT id, article, de, ru 
        FROM words 
        WHERE article IN ('die', 'der', 'das')
        ORDER BY id DESC
        LIMIT 10
    """)
    
    examples = cur.fetchall()
    for row in examples:
        print(f"  {row[1]:6} {row[2]:30} ({row[3]})")
    
    cur.close()
    conn.close()
    
    print("\n" + "="*60)
    print(f"✅ Готово! Исправлено всего: {fixed_die + fixed_der + fixed_das + fixed_trim} записей")
    print("="*60 + "\n")


if __name__ == "__main__":
    print("="*60)
    print("ИСПРАВЛЕНИЕ ДУБЛИРУЮЩИХСЯ АРТИКЛЕЙ")
    print("="*60 + "\n")
    
    confirm = input("Выполнить исправление? (y/n): ")
    if confirm.lower() != 'y':
        print("❌ Отменено")
        sys.exit(0)
    
    fix_duplicates()
