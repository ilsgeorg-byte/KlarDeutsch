import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Загружаем переменные окружения из .env.local (который лежит в корне проекта)
# Указываем путь к корню, так как db.py лежит в api/
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.local')
load_dotenv(dotenv_path)

def get_db_connection():
    url = os.environ.get("POSTGRES_URL")
    if not url:
        # Если переменной нет, попробуем найти другую (Prisma иногда дает другое имя)
        url = os.environ.get("DATABASE_URL")
    
    if not url:
        print("Ошибка: POSTGRES_URL не найдена!")
        print(f"Доступные переменные окружения: {list(os.environ.keys())[:10]}")
        raise Exception("POSTGRES_URL не найдена в переменных окружения")

    try:
        conn = psycopg2.connect(url)
        print("✅ Успешное подключение к БД")
        return conn
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {str(e)}")
        raise

def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Таблица слов
        cur.execute("""
            CREATE TABLE IF NOT EXISTS words (
                id SERIAL PRIMARY KEY,
                level VARCHAR(10) NOT NULL,
                topic VARCHAR(100),
                de TEXT NOT NULL,
                ru TEXT NOT NULL,
                article VARCHAR(10),
                example_de TEXT,
                example_ru TEXT,
                audio_url TEXT
            );
        """)
        
        # Таблица прогресса
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_words (
                word_id INTEGER REFERENCES words(id),
                status VARCHAR(20) DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (word_id)
            );
        """)
        
        # Таблица записей в дневнике
        cur.execute("""
            CREATE TABLE IF NOT EXISTS diary_entries (
                id SERIAL PRIMARY KEY,
                original_text TEXT NOT NULL,
                corrected_text TEXT NOT NULL,
                explanation TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        print("Database initialized!")
    except Exception as e:
        print(f"Error initializing DB: {e}")

if __name__ == "__main__":
    init_db()
