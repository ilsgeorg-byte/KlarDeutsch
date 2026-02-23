# api/clear_verb_articles.py
# Запуск: python api/clear_verb_articles.py

import os
import psycopg2
from dotenv import load_dotenv

# грузим .env.local из корня проекта
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env.local")
load_dotenv(dotenv_path)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL не найден в .env.local")

SQL_UPDATE = """
UPDATE words
SET article = NULL
WHERE topic = 'Глаголы';
"""

def main():
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        cur.execute(SQL_UPDATE)
        affected = cur.rowcount
        conn.commit()
        print(f"Готово. Обновлено строк: {affected}")
    except Exception as e:
        conn.rollback()
        print("Ошибка, транзакция откатена:", e)
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()
