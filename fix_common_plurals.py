
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import json

# Загружаем переменные окружения
dotenv_path = os.path.join(os.path.dirname(__file__), '.env.local')
load_dotenv(dotenv_path)

def fix_common_plurals():
    url = os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL")
    if not url:
        print("POSTGRES_URL not found")
        return

    conn = psycopg2.connect(url, cursor_factory=RealDictCursor)
    cur = conn.cursor()
    
    # Список базовых слов и их правильных данных
    common_fixes = [
        ("Baum", "der", "дерево", "die Bäume"),
        ("Meer", "das", "море", "die Meere"),
        ("Zimmer", "das", "комната", "die Zimmer"),
        ("Frau", "die", "женщина", "die Frauen"),
        ("Mann", "der", "мужчина", "die Männer"),
        ("Kind", "das", "ребенок", "die Kinder"),
        ("Haus", "das", "дом", "die Häuser"),
        ("Buch", "das", "книга", "die Bücher"),
        ("Tisch", "der", "стол", "die Tische"),
        ("Stuhl", "der", "стул", "die Stühle"),
        ("Auge", "das", "глаз", "die Augen"),
        ("Hand", "die", "рука", "die Hände"),
        ("Fuß", "der", "нога", "die Füße"),
        ("Stadt", "die", "город", "die Städte"),
        ("Land", "das", "страна/земля", "die Länder"),
        ("Wort", "das", "слово", "die Wörter"),
        ("Tag", "der", "день", "die Tage"),
        ("Jahr", "das", "год", "die Jahre"),
        ("Monat", "der", "месяц", "die Monate"),
        ("Woche", "die", "неделя", "die Wochen")
    ]
    
    found = 0
    for word, article, ru, plural in common_fixes:
        # Ищем слово
        cur.execute("""
            SELECT id, de, ru, article, plural 
            FROM words 
            WHERE de ILIKE %s OR de ILIKE %s
        """, (word, f"{article} {word}"))
        rows = cur.fetchall()
        
        for row in rows:
            if row['plural'] is None or row['plural'] == "" or row['plural'] == "None":
                print(f"Fixing {row['de']} (ID: {row['id']}) -> Plural: {plural}")
                cur.execute("UPDATE words SET plural = %s, article = %s, ai_checked_at = NOW() WHERE id = %s", (plural, article, row['id']))
                found += 1
                
    conn.commit()
    print(f"Fixed {found} common plurals.")
    cur.close()
    conn.close()

if __name__ == "__main__":
    fix_common_plurals()
