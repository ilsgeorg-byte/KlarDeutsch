import os
import psycopg2
from dotenv import load_dotenv

load_dotenv('.env.local')
url = os.getenv("DATABASE_URL")

def fix_word():
    conn = psycopg2.connect(url)
    cur = conn.cursor()
    
    # 1. Сначала найдем ID этого слова (или слов, если их несколько)
    cur.execute("SELECT id FROM words WHERE de = 'stehlen';")
    rows = cur.fetchall()
    
    if not rows:
        print("❌ Слово 'stehlen' не найдено в базе.")
        return

    for (word_id,) in rows:
        print(f"🔧 Исправляю карточку ID {word_id}...")
        
        # Правильные данные для глагола stehlen:
        # Infinitiv: stehlen
        # Präsens: stiehlt
        # Präteritum: stahl
        # Partizip II: hat gestohlen
        verb_forms = "stehlen, stiehlt, stahl, hat gestohlen"
        
        # Обновляем: убираем артикль и множественное число (это же глагол!)
        cur.execute("""
            UPDATE words 
            SET article = NULL, 
                plural = NULL, 
                verb_forms = %s,
                ru = 'красть',
                ai_checked_at = NOW()
            WHERE id = %s
        """, (verb_forms, word_id))
    
    conn.commit()
    print("✅ Карточка 'stehlen' успешно исправлена!")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    fix_word()
