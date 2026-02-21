import os
import psycopg2
import json
from dotenv import load_dotenv

# Загружаем URL базы
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.local')
load_dotenv(dotenv_path)

def update_test_word():
    url = os.environ.get("POSTGRES_URL")
    conn = psycopg2.connect(url)
    cur = conn.cursor()
    
    # 1. Обновляем слово groß (или добавляем, если его нет)
    examples_json = json.dumps([
        {"de": "Er ist sehr groß.", "ru": "Он очень высокий."},
        {"de": "Ein großes Haus.", "ru": "Большой дом."},
        {"de": "Wie groß bist du?", "ru": "Какого ты роста?"}
    ])
    
    cur.execute("""
        UPDATE words 
        SET article = '', 
            synonyms = 'riesig, gewaltig', 
            antonyms = 'klein, winzig', 
            collocations = 'groß werden, zu groß sein',
            examples = %s
        WHERE de = 'groß';
    """, (examples_json,))
    
    # 2. Обновляем слово Hund (собака)
    examples_hund = json.dumps([
        {"de": "Der Hund bellt laut.", "ru": "Собака громко лает."},
        {"de": "Ich gehe mit dem Hund spazieren.", "ru": "Я иду гулять с собакой."},
        {"de": "Ein treuer Hund.", "ru": "Верная собака."}
    ])
    
    cur.execute("""
        UPDATE words 
        SET article = 'der', 
            plural = 'die Hunde',
            synonyms = 'Haustier, Vierbeiner', 
            collocations = 'einen Hund halten, Gassi gehen',
            examples = %s
        WHERE de = 'Hund';
    """, (examples_hund,))
    
    print(f"Обновлено строк (Hund): {cur.rowcount}")
    conn.commit()
    cur.close()
    conn.close()
    print("Тестовые данные успешно загружены в базу!")

if __name__ == "__main__":
    update_test_word()
