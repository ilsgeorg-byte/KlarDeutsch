
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import json

# Загружаем переменные окружения
dotenv_path = os.path.join(os.path.dirname(__file__), '.env.local')
load_dotenv(dotenv_path)

def fix_schild():
    url = os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL")
    if not url:
        print("POSTGRES_URL not found")
        return

    conn = psycopg2.connect(url, cursor_factory=RealDictCursor)
    cur = conn.cursor()
    
    # 1. Находим все слова с переводом "Наместник"
    cur.execute("SELECT id, de, ru FROM words WHERE ru ILIKE '%Наместник%'")
    rows = cur.fetchall()
    
    if rows:
        print(f"Found {len(rows)} words with 'Наместник':")
        for row in rows:
            print(f"ID: {row['id']}, DE: {row['de']}, RU: {row['ru']}")
            
            # Если это Schild, исправляем
            if 'Schild' in row['de']:
                print(f"Fixing Schild (ID: {row['id']})...")
                
                new_ru = "вывеска, табличка, знак"
                new_plural = "die Schilder"
                new_examples = [
                    {"de": "Das Schild an der Tür sagt 'Geschlossen'.", "ru": "Табличка на двери гласит 'Закрыто'."},
                    {"de": "Folgen Sie den Schildern zum Bahnhof.", "ru": "Следуйте по указателям к вокзалу."},
                    {"de": "Das Schild ist aus Metall.", "ru": "Вывеска сделана из металла."}
                ]
                
                cur.execute("""
                    UPDATE words 
                    SET ru = %s, 
                        plural = %s, 
                        examples = %s,
                        article = 'das',
                        ai_checked_at = NOW()
                    WHERE id = %s
                """, (new_ru, new_plural, json.dumps(new_examples), row['id']))
                print("Fixed!")
    else:
        print("No words with 'Наместник' found (except maybe those already fixed or if search failed).")

    # 2. На всякий случай ищем das Schild по DE
    cur.execute("SELECT id, de, ru, plural FROM words WHERE de ILIKE 'das Schild' OR de = 'Schild'")
    rows = cur.fetchall()
    for row in rows:
        if row['plural'] is None or row['plural'] == "" or row['ru'] == "Наместник":
            print(f"Fixing das Schild by DE (ID: {row['id']})...")
            new_ru = "вывеска, табличка, знак"
            new_plural = "die Schilder"
            new_examples = [
                {"de": "Das Schild an der Tür sagt 'Geschlossen'.", "ru": "Табличка на двери гласит 'Закрыто'."},
                {"de": "Folgen Sie den Schildern zum Bahnhof.", "ru": "Следуйте по указателям к вокзалу."},
                {"de": "Das Schild ist aus Metall.", "ru": "Вывеска сделана из металла."}
            ]
            cur.execute("""
                UPDATE words 
                SET ru = %s, 
                    plural = %s, 
                    examples = %s,
                    article = 'das',
                    ai_checked_at = NOW()
                WHERE id = %s
            """, (new_ru, new_plural, json.dumps(new_examples), row['id']))
            print("Fixed!")

    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    fix_schild()
