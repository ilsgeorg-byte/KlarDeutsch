"""
Миграция для добавления новых колонок в таблицу words
Запустить: python add_word_columns.py
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

# Загружаем переменные окружения
env_path = os.path.join(os.path.dirname(__file__), '..', '.env.local')
load_dotenv(env_path)

url = os.environ.get("POSTGRES_URL")
if not url:
    print("POSTGRES_URL не найдена!")
    sys.exit(1)

try:
    # Подключаемся к БД
    conn = psycopg2.connect(url)
    cur = conn.cursor()
    
    print("Подключено к базе данных")
    
    # Добавляем колонки если их нет
    columns = [
        ("synonyms", "TEXT"),
        ("antonyms", "TEXT"),
        ("collocations", "TEXT"),
    ]
    
    for col_name, col_type in columns:
        try:
            cur.execute(f"""
                ALTER TABLE words 
                ADD COLUMN IF NOT EXISTS {col_name} {col_type}
            """)
            print(f"✓ Колонка {col_name} добавлена (или уже существует)")
        except Exception as e:
            print(f"✗ Ошибка при добавлении {col_name}: {e}")
    
    # Добавляем колонку plural если её нет
    try:
        cur.execute("""
            ALTER TABLE words 
            ADD COLUMN IF NOT EXISTS plural TEXT
        """)
        print(f"✓ Колонка plural добавлена (или уже существует)")
    except Exception as e:
        print(f"✗ Ошибка при добавлении plural: {e}")
    
    # Коммитим изменения
    conn.commit()
    print("\n✓ Миграция завершена успешно!")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"\n✗ Ошибка: {e}")
    sys.exit(1)
