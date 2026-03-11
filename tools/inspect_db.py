import os
import psycopg2
from urllib.parse import urlparse
from dotenv import load_dotenv

# грузим .env.local из корня проекта (как у тебя)
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env.local")
load_dotenv(dotenv_path)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL не найден в .env.local")

def get_connection():
    # psycopg2 понимает URL напрямую
    return psycopg2.connect(DATABASE_URL)

def list_tables():
    conn = get_connection()
    cur = conn.cursor()
    # показываем только пользовательские таблицы в public
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return tables

def list_columns(table_name: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position;
    """, (table_name,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def main():
    print("Таблицы в схеме public:")
    tables = list_tables()
    for t in tables:
        print(f"- {t}")

    # здесь можешь сразу подставить свою таблицу, например 'words'
    table_name = input("\nВведи имя таблицы, для которой показать колонки: ").strip()
    if not table_name:
        return

    cols = list_columns(table_name)
    print(f"\nКолонки таблицы {table_name}:")
    for name, dtype in cols:
        print(f"- {name} ({dtype})")

if __name__ == "__main__":
    main()
