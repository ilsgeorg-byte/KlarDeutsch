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
        print("Successfully connected to DB")
        return conn
    except Exception as e:
        print(f"Error connecting to DB: {str(e)}")
        raise

def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Таблица пользователей
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Таблица слов
        cur.execute("""
            CREATE TABLE IF NOT EXISTS words (
                id SERIAL PRIMARY KEY,
                level VARCHAR(10) NOT NULL,
                topic VARCHAR(100),
                de TEXT NOT NULL,
                ru TEXT NOT NULL,
                article VARCHAR(10),
                verb_forms TEXT,
                example_de TEXT,
                example_ru TEXT,
                audio_url TEXT,
                examples JSONB,
                plural TEXT,
                user_id INTEGER REFERENCES users(id),
                UNIQUE(de, ru, user_id)
            );
        """)
        
        # Таблица прогресса (SRS) - теперь привязана к пользователю
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_words (
                user_id INTEGER REFERENCES users(id),
                word_id INTEGER REFERENCES words(id),
                ease_factor FLOAT DEFAULT 2.5,
                interval INTEGER DEFAULT 0,
                reps INTEGER DEFAULT 0,
                next_review TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20) DEFAULT 'learning',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, word_id)
            );
        """)
        
        # Миграция для старой схемы
        cur.execute("ALTER TABLE user_words ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id);")
        
        # Если есть строки с NULL user_id, заполняем их первым попавшимся юзером
        cur.execute("SELECT id FROM users ORDER BY id LIMIT 1")
        first_user = cur.fetchone()
        if first_user:
            cur.execute("UPDATE user_words SET user_id = %s WHERE user_id IS NULL", (first_user[0],))
            
        # Убеждаемся, что первичный ключ правильный (составной)
        cur.execute("SELECT conname FROM pg_constraint WHERE conrelid = 'user_words'::regclass AND contype = 'p'")
        pk_name = cur.fetchone()
        if not pk_name:
            cur.execute("ALTER TABLE user_words ADD PRIMARY KEY (user_id, word_id)")
            
        cur.execute("ALTER TABLE words ADD COLUMN IF NOT EXISTS verb_forms TEXT;")
        cur.execute("ALTER TABLE words ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id);")
        
        # Обновляем уникальный индекс для слов (чтобы разные юзеры могли иметь одинаковые личные слова)
        try:
            cur.execute("ALTER TABLE words DROP CONSTRAINT IF EXISTS words_de_ru_key;")
            # Уникальность по de, ru и user_id (где user_id может быть NULL)
            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_words_de_ru_public ON words (de, ru) WHERE user_id IS NULL;")
            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_words_de_ru_private ON words (de, ru, user_id) WHERE user_id IS NOT NULL;")
        except Exception as e:
            print(f"Warning during words index update: {e}")
            conn.rollback() 

        # Таблица аудиозаписей
        cur.execute("""
            CREATE TABLE IF NOT EXISTS recordings (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                filename TEXT NOT NULL,
                url TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_data BYTEA,
                mimetype TEXT
            );
        """)
        cur.execute("ALTER TABLE recordings ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id);")

        # Таблица избранного
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_favorites (
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                word_id INTEGER REFERENCES words(id) ON DELETE CASCADE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, word_id)
            );
        """)

        # Таблица заметок пользователя к словам
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_word_notes (
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                word_id INTEGER REFERENCES words(id) ON DELETE CASCADE,
                note TEXT NOT NULL DEFAULT '',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, word_id)
            );
        """)

        # МИГРАЦИИ: Добавляем новые колонки в таблицу words (если их еще нет)
        cur.execute("ALTER TABLE words ADD COLUMN IF NOT EXISTS examples JSONB;")
        cur.execute("ALTER TABLE words ADD COLUMN IF NOT EXISTS plural TEXT;")
        
        # --- НОВЫЕ ЛИНГВИСТИЧЕСКИЕ КОЛОНКИ ---
        cur.execute("ALTER TABLE words ADD COLUMN IF NOT EXISTS synonyms TEXT;")
        cur.execute("ALTER TABLE words ADD COLUMN IF NOT EXISTS antonyms TEXT;")
        cur.execute("ALTER TABLE words ADD COLUMN IF NOT EXISTS collocations TEXT;")
        # -----------------------------------
        
        conn.commit()
        cur.close()
        conn.close()
        print("Database initialized successfully with new linguistic columns!")
    except Exception as e:
        print(f"Error initializing DB: {e}")

if __name__ == "__main__":
    init_db()
