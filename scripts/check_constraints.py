import os
import psycopg2
from dotenv import load_dotenv

def check_constraints():
    env_path = os.path.join(os.getcwd(), '.env.local')
    load_dotenv(env_path)
    url = os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL")
    
    if not url:
        print("Error: No database URL found")
        return

    try:
        conn = psycopg2.connect(url)
        cur = conn.cursor()
        cur.execute("""
            SELECT conname
            FROM pg_constraint
            WHERE conrelid = 'words'::regclass AND contype = 'u';
        """)
        constraints = cur.fetchall()
        print(f"Unique constraints on 'words' table: {[c[0] for c in constraints]}")
        
        cur.execute("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'words';
        """)
        indexes = cur.fetchall()
        print("Indexes on 'words' table:")
        for idx in indexes:
            print(f"  {idx[0]}: {idx[1]}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_constraints()
