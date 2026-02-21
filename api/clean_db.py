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

def clean_numbers():
    print("Подключаюсь к базе для удаления цифрового мусора и дубликатов...")
    try:
        conn = psycopg2.connect(url)
        cur = conn.cursor()
        
        # Шаг 1: Находим все слова, которые состоят только из цифр, пробелов, тире или точек
        # Regex ^[\d\s\-\.]+$ ловит строки вроде "84886454459", "12-34", " 456 "
        cur.execute("SELECT id, de FROM words WHERE de ~ '^[\d\s\-\.]+$';")
        junk_words = cur.fetchall()
        
        print(f"Найдено мусорных карточек (цифры): {len(junk_words)}")
        
        deleted_count = 0
        for junk_id, junk_de in junk_words:
            # Сначала удаляем связи из user_words (чтобы не было ошибки foreign key)
            cur.execute("DELETE FROM user_words WHERE word_id = %s;", (junk_id,))
            
            # Затем удаляем само мусорное слово
            cur.execute("DELETE FROM words WHERE id = %s;", (junk_id,))
            deleted_count += 1
            
        conn.commit()
        print(f"✅ Успешно удалено мусорных карточек: {deleted_count}")
        
        # Шаг 2: Удаляем слова "Wort1000", если они вдруг остались
        cur.execute("SELECT id FROM words WHERE de LIKE 'Wort%';")
        test_words = cur.fetchall()
        
        if test_words:
            print(f"Найдено тестовых слов (Wort...): {len(test_words)}")
            for test_id, in test_words:
                cur.execute("DELETE FROM user_words WHERE word_id = %s;", (test_id,))
                cur.execute("DELETE FROM words WHERE id = %s;", (test_id,))
            conn.commit()
            print(f"✅ Успешно удалено тестовых слов: {len(test_words)}")

        # Финальная проверка
        cur.execute("SELECT count(*) FROM words;")
        print(f"📊 Всего нормальных слов в базе осталось: {cur.fetchone()[0]}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        if conn: conn.rollback()
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals() and conn: conn.close()

if __name__ == "__main__":
    clean_numbers()
