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

def get_conn():
    return psycopg2.connect(url)

def safe_delete_word(cur, word_id, word_de):
    """Безопасно удаляет слово, очищая все внешние ключи"""
    # Список таблиц, которые ссылаются на words.id
    tables = ["user_words", "user_favorites", "user_word_notes"]
    
    for table in tables:
        cur.execute(f"DELETE FROM {table} WHERE word_id = %s;", (word_id,))
    
    # Теперь удаляем само слово
    cur.execute("DELETE FROM words WHERE id = %s;", (word_id,))
    return True

def clean_database():
    print("🚀 Начинаю генеральную уборку базы данных...")
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        
        # --- ШАГ 1: Цифровой мусор ---
        cur.execute("SELECT id, de FROM words WHERE de ~ '^[\\d\\s\\-\\.]+$';")
        junk_numbers = cur.fetchall()
        print(f"1️⃣  Найдено цифрового мусора: {len(junk_numbers)}")
        
        for j_id, j_de in junk_numbers:
            safe_delete_word(cur, j_id, j_de)
        
        # --- ШАГ 2: Длинные конструкции (предложения) ---
        # Считаем количество слов в строке 'de'. Если слов > 4 (т.е. пробелов >= 4), это предложение.
        # Регулярка [^ ]+ ищет слова, разделенные пробелами.
        cur.execute("SELECT id, de FROM words WHERE array_length(regexp_split_to_array(trim(de), '\\s+'), 1) > 4;")
        phrases = cur.fetchall()
        print(f"2️⃣  Найдено длинных конструкций (предложений): {len(phrases)}")
        
        for p_id, p_de in phrases:
            print(f"   🗑️ Удаляю фразу: {p_de[:50]}...")
            safe_delete_word(cur, p_id, p_de)

        # --- ШАГ 3: Тестовые слова (Wort1000 и т.д.) ---
        cur.execute("SELECT id, de FROM words WHERE de LIKE 'Wort%';")
        test_words = cur.fetchall()
        print(f"3️⃣  Найдено тестовых слов (Wort...): {len(test_words)}")
        
        for t_id, t_de in test_words:
            safe_delete_word(cur, t_id, t_de)

        conn.commit()
        print("\n✨ Уборка завершена успешно!")
        
        # Итоговая статистика
        cur.execute("SELECT count(*) FROM words;")
        print(f"📊 Всего качественных слов в базе: {cur.fetchone()[0]}")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        if conn: conn.rollback()
    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == "__main__":
    clean_database()
