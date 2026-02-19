import os
import psycopg2
from dotenv import load_dotenv

def check_schema():
    env_path = os.path.join(os.getcwd(), '.env.local')
    load_dotenv(env_path)
    url = os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL")
    
    if not url:
        print("Error: No database URL found")
        return

    try:
        conn = psycopg2.connect(url)
        cur = conn.cursor()
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'words'")
        columns = cur.fetchall()
        print(f"Columns in 'words' table: {[col[0] for col in columns]}")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_schema()
