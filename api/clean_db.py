import os
import psycopg2
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.local')
load_dotenv(dotenv_path)

url = os.getenv("DATABASE_URL")

if not url:
    print("❌ Ошибка: Не найден DATABASE_URL")
    exit(1)

def fix_commas_in_db():
    print("Подключаюсь к базе данных для исправления запятых...")
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(url)
        cur = conn.cursor()
        
        # Исправляем колонки: synonyms, antonyms, collocations
        # Эта команда делает две вещи:
        # 1. Заменяет все ", " на "," (чтобы убрать лишние пробелы, если они были)
        # 2. Заменяет все "," на ", " (чтобы гарантировать ровно один пробел после каждой запятой)
        
        update_query = """
        UPDATE words 
        SET 
            synonyms = REPLACE(REPLACE(synonyms, ', ', ','), ',', ', '),
            antonyms = REPLACE(REPLACE(antonyms, ', ', ','), ',', ', '),
            collocations = REPLACE(REPLACE(collocations, ', ', ','), ',', ', ')
        WHERE synonyms IS NOT NULL OR antonyms IS NOT NULL OR collocations IS NOT NULL;
        """
        
        cur.execute(update_query)
        updated_count = cur.rowcount
        conn.commit()
        
        print(f"✅ Успешно исправлены пробелы после запятых в {updated_count} словах!")
        
    except Exception as e:
        print(f"❌ Ошибка при обновлении: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
            print("Соединение закрыто.")

if __name__ == "__main__":
    fix_commas_in_db()
