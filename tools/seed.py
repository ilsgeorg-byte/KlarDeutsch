import os
import sys

# Добавляем путь к текущей директории, чтобы импортировать db и data_words
sys.path.append(os.path.dirname(__file__))

from db import get_db_connection
from data_words import WORDS

def seed_data():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Опционально: очистить старые, чтобы не дублировать при тестах
        # cur.execute("TRUNCATE words CASCADE;")
        
        count = 0
        for w in WORDS:
            # Проверяем, нет ли такого слова уже (по de + ru)
            cur.execute("SELECT id FROM words WHERE de = %s AND ru = %s", (w['de'], w['ru']))
            if cur.fetchone():
                continue

            cur.execute("""
                INSERT INTO words (level, topic, de, ru, article, example_de, example_ru)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (w['level'], w['topic'], w['de'], w['ru'], w['article'], w['example_de'], w['example_ru']))
            count += 1
        
        conn.commit()
        cur.close()
        conn.close()
        print(f"Words seeded! Added {count} new words.")
    except Exception as e:
        print(f"Error seeding data: {e}")

if __name__ == "__main__":
    seed_data()
