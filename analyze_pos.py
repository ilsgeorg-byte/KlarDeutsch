import os
import psycopg2
from dotenv import load_dotenv

load_dotenv('.env.local')

def analyze_parts_of_speech():
    url = os.environ.get("POSTGRES_URL")
    try:
        conn = psycopg2.connect(url)
        cur = conn.cursor()
        
        # Глаголы
        cur.execute("SELECT COUNT(*) FROM words WHERE topic LIKE '%Глагол%' OR topic LIKE '%глагол%'")
        verbs_count = cur.fetchone()[0]
        
        # Прилагательные
        cur.execute("SELECT COUNT(*) FROM words WHERE topic LIKE '%Прилагательн%' OR topic LIKE '%прилагательн%'")
        adj_count = cur.fetchone()[0]
        
        # Наречия / Союзы / Разное без артиклей
        cur.execute("SELECT COUNT(*) FROM words WHERE (article IS NULL OR article = '') AND NOT (topic LIKE '%Прилагательн%' OR topic LIKE '%прилагательн%' OR topic LIKE '%Глагол%' OR topic LIKE '%глагол%')")
        misc_no_article = cur.fetchone()[0]
        
        # Существительные
        cur.execute("SELECT COUNT(*) FROM words WHERE (article IS NOT NULL AND article != '')")
        nouns_count = cur.fetchone()[0]
        
        print(f"Verbs: {verbs_count}")
        print(f"Adjectives: {adj_count}")
        print(f"Misc (no article): {misc_no_article}")
        print(f"Nouns: {nouns_count}")
        print(f"Total: {verbs_count + adj_count + misc_no_article + nouns_count}")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze_parts_of_speech()
