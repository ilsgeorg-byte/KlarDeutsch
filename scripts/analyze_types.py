import os
import psycopg2
from dotenv import load_dotenv

load_dotenv('.env.local')

def analyze_word_types():
    url = os.environ.get("POSTGRES_URL")
    try:
        conn = psycopg2.connect(url)
        cur = conn.cursor()
        
        print("Total words:", end=" ")
        cur.execute("SELECT COUNT(*) FROM words")
        print(cur.fetchone()[0])
        
        print("\nDistribution by Category (Topic):")
        cur.execute("SELECT topic, COUNT(*) FROM words GROUP BY topic ORDER BY COUNT(*) DESC")
        for topic, count in cur.fetchall():
            print(f"- {topic}: {count}")
            
        print("\nWords with/without Articles:")
        cur.execute("SELECT (article IS NOT NULL AND article != ''), COUNT(*) FROM words GROUP BY (article IS NOT NULL AND article != '')")
        for has_article, count in cur.fetchall():
            type_label = "Nouns (has article)" if has_article else "Other (no article)"
            print(f"- {type_label}: {count}")
            
        print("\nSample 'Other' words (Potential Verbs/Adjectives):")
        cur.execute("SELECT de, ru, topic FROM words WHERE article IS NULL OR article = '' LIMIT 20")
        for de, ru, topic in cur.fetchall():
            print(f"- {de} ({ru}) [{topic}]")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze_word_types()
