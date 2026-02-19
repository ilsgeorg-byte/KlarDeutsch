import os
import sys

# Add the current directory to sys.path
sys.path.append(os.path.dirname(__file__))

from db import get_db_connection
from goethe_data import GOETHE_WORDS
from goethe_verbs_adj import GOETHE_VERBS_ADJ

def seed_final():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Combine all sources
        all_sources = [GOETHE_WORDS, GOETHE_VERBS_ADJ]
        
        total_added = 0
        total_skipped = 0
        
        for source in all_sources:
            for w in source:
                # Check if word already exists (by de and ru to be safe, or just de)
                cur.execute("SELECT id FROM words WHERE de = %s AND ru = %s", (w['de'], w['ru']))
                if cur.fetchone():
                    total_skipped += 1
                    continue

                cur.execute("""
                    INSERT INTO words (level, topic, de, ru, article, example_de, example_ru)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (w['level'], w['topic'], w['de'], w['ru'], w.get('article', ''), w.get('example_de', ''), w.get('example_ru', '')))
                total_added += 1
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"Seed Final complete.")
        print(f"Added: {total_added}")
        print(f"Skipped (already exists): {total_skipped}")
        print(f"Total in source: {total_added + total_skipped}")
        
    except Exception as e:
        print(f"Error seeding final data: {e}")

if __name__ == "__main__":
    seed_final()
