
import os, sys, psycopg2
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env.local'))

def deep_cleanup():
    conn = psycopg2.connect(os.environ.get("POSTGRES_URL"))
    cur = conn.cursor()
    
    # 1. Очищаем verb_forms у СУЩЕСТВИТЕЛЬНЫХ (начинаются с большой буквы)
    # Исключение: слова из одной буквы или специфические случаи, но в целом в нем. яз. это работает.
    cur.execute("UPDATE words SET verb_forms = '' WHERE de ~ '^[A-ZÄÖÜ]' AND verb_forms IS NOT NULL AND verb_forms != ''")
    rows1 = cur.rowcount
    
    # 2. Очищаем article и plural у ГЛАГОЛОВ (начинаются с маленькой буквы)
    cur.execute("UPDATE words SET article = '', plural = '' WHERE de ~ '^[a-zäöü]' AND (article != '' OR plural != '')")
    rows2 = cur.rowcount
    
    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ Deep cleanup finished!")
    print(f"Removed verb_forms from {rows1} nouns")
    print(f"Removed articles/plurals from {rows2} verbs")

if __name__ == "__main__":
    deep_cleanup()
