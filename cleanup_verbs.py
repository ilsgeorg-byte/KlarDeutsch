
import os, sys, psycopg2
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env.local'))

def cleanup():
    conn = psycopg2.connect(os.environ.get("POSTGRES_URL"))
    cur = conn.cursor()
    
    # 1. Если есть формы глагола — артикль и мн.ч. точно не нужны
    cur.execute("UPDATE words SET article = '', plural = '' WHERE verb_forms IS NOT NULL AND verb_forms != ''")
    rowcount1 = cur.rowcount
    
    # 2. Если слово начинается с маленькой буквы и заканчивается на "en" (типичный глагол), 
    # а в нем почему-то стоит артикль
    cur.execute("UPDATE words SET article = '', plural = '' WHERE de ~ '^[a-z].*en$' AND article IS NOT NULL AND article != ''")
    rowcount2 = cur.rowcount
    
    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ Cleanup finished!")
    print(f"Fixed {rowcount1} words with verb_forms")
    print(f"Fixed {rowcount2} words with verb-like endings")

if __name__ == "__main__":
    cleanup()
