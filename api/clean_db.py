import os
import psycopg2
from dotenv import load_dotenv

# Загружаем переменные из .env.local
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.local')
load_dotenv(dotenv_path)

url = os.getenv("DATABASE_URL")

if not url:
    print("❌ Ошибка: Не найден DATABASE_URL")
    exit(1)

def clean_test_words():
    print("Подключаюсь к базе данных для очистки...")
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(url)
        cur = conn.cursor()
        
        # Удаляем все строки, где колонка 'de' начинается на 'Wort'
        cur.execute("DELETE FROM words WHERE de LIKE 'Wort%';")
        
        deleted_count = cur.rowcount
        conn.commit()
        
        print(f"✅ Успешно удалено тестовых слов: {deleted_count}!")
        
    except Exception as e:
        print(f"❌ Ошибка при удалении: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
            print("Соединение закрыто.")

if __name__ == "__main__":
    clean_test_words()
