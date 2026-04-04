import os
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv('.env.local')

POSTGRES_URL = os.getenv('POSTGRES_URL')

def check_db_time():
    conn = psycopg2.connect(POSTGRES_URL)
    cur = conn.cursor()
    
    cur.execute("SELECT NOW(), CURRENT_DATE")
    row = cur.fetchone()
    print(f"DB NOW(): {row[0]}")
    print(f"DB CURRENT_DATE: {row[1]}")
    print(f"System Time: {datetime.now()}")
    
    # Check if words marked as checked today are indeed today
    cur.execute("SELECT id, de, ai_checked_at FROM words WHERE ai_checked_at IS NOT NULL ORDER BY ai_checked_at DESC LIMIT 5")
    rows = cur.fetchall()
    print("\n--- Last 5 updated words ---")
    for r in rows:
        print(r)
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_db_time()
