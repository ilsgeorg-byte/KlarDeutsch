import os
import json
import re
import time 
import psycopg2 
from dotenv import load_dotenv 
from groq import Groq

# Загружаем переменные
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.local')
load_dotenv(dotenv_path)

GROQ_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_KEY:
    print("❌ Ошибка: GROQ_API_KEY не установлен в .env.local")
    exit(1)

groq_client = Groq(api_key=GROQ_KEY)



def get_linguistic_data_groq(de_word, ru_word, level):
    prompt = f"""
    Ты эксперт-лингвист немецкого языка. Дай данные для слова (уровень {level}): {de_word} (перевод: {ru_word}).
    
    Верни строго JSON объект следующего формата. Выведи ТОЛЬКО JSON, без приветствий и пояснений:
    {{
      "synonyms": "2-3 синонима на немецком через запятую, или пустая строка",
      "antonyms": "1-2 антонима на немецком через запятую, или пустая строка",
      "collocations": "2 типичных словосочетания с этим словом на немецком",
      "examples": [
        {{"de": "Простой пример 1 на немецком", "ru": "Перевод 1"}},
        {{"de": "Пример 2 чуть сложнее", "ru": "Перевод 2"}},
        {{"de": "Пример 3 (вопрос или отрицание)", "ru": "Перевод 3"}}
      ]
    }}
    """
    
    def get_linguistic_data_groq(de_word, ru_word, level):
        prompt = f"""
    Выведи строго JSON объект для немецкого слова "{de_word}" (перевод: {ru_word}, уровень {level}).
    Пиши кратко. Никаких лишних слов, только этот JSON:
    {{
      "synonyms": "2 синонима через запятую",
      "antonyms": "1 антоним",
      "collocations": "2 коротких словосочетания",
      "examples": [
        {{"de": "Короткий пример 1.", "ru": "Перевод 1."}},
        {{"de": "Короткий пример 2.", "ru": "Перевод 2."}},
        {{"de": "Короткий пример 3.", "ru": "Перевод 3."}}
      ]
    }}
    """
    
    try:
        completion = groq_client.chat.completions.create(
            # Попробуй поменять модель, если Llama всё равно спотыкается:
            model="llama-3.1-8b-instant", # или "gemma2-9b-it" 
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,    # <-- УВЕЛИЧЕНО до 0.6, чтобы избежать "заедания"
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        text = completion.choices[0].message.content
        return json.loads(text)
        
    except Exception as e:
        print(f"\n[!] Ошибка API для {de_word}: {e}")
        # Возвращаем пустые данные, чтобы скрипт не падал, а шел дальше!
        return {
            "synonyms": "", "antonyms": "", "collocations": "",
            "examples": [{"de": "Fehler beim Laden", "ru": "Ошибка загрузки"}]
        }


    
    text = completion.choices[0].message.content
    
    # Регулярное выражение: вырезаем всё строго от первой { до последней }
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        text = match.group(0)
        
    return json.loads(text)

    
    
    completion = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant", 
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=1000,
    )
    
    text = completion.choices[0].message.content
    text = text.replace('```json', '').replace('```', '').strip()
    return json.loads(text)

def update_database():
    url = os.environ.get("POSTGRES_URL")
    if not url:
        print("❌ Ошибка: POSTGRES_URL не найдена в .env.local")
        return
        
    conn = psycopg2.connect(url)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, de, ru, level 
        FROM words 
        WHERE (synonyms IS NULL OR synonyms = '') 
           OR (examples IS NULL OR jsonb_array_length(examples) < 2)
        ORDER BY id ASC
        LIMIT 100;
    """)
    
    words_to_update = cur.fetchall()
    
    if not words_to_update:
        print("🎉 База полностью заполнена! Пустых слов больше нет.")
        cur.close()
        conn.close()
        return

    print(f"🚀 Найдено {len(words_to_update)} слов для обогащения через Groq (Батч из 100 штук)...")
    success_count = 0

    for i, row in enumerate(words_to_update, 1):
        word_id, de, ru, level = row
        print(f"\nДАННЫЕ ИЗ БАЗЫ: ID={word_id}, Немецкое={de}, Русское={ru}")

        print(f"[{i}/{len(words_to_update)}] Обрабатываю: {de}...", end=" ", flush=True)
        
        try:
            data = get_linguistic_data_groq(de, ru, level)
            
            if data and isinstance(data, dict):
                examples_json = json.dumps(data.get("examples", []))
                
                cur.execute("""
                    UPDATE words 
                    SET synonyms = %s, antonyms = %s, collocations = %s, examples = %s
                    WHERE id = %s
                """, (
                    data.get("synonyms", ""),
                    data.get("antonyms", ""),
                    data.get("collocations", ""),
                    examples_json,
                    word_id
                ))
                conn.commit()
                print("✅")
                success_count += 1
        except Exception as err:
            print(f"❌ Ошибка: {err}")
            conn.rollback()
        
        # Groq очень быстрый, но оставим 0.5с паузы для избежания Rate Limits
        time.sleep(2)

    cur.close()
    conn.close()
    print(f"\n✨ Готово! Успешно обновлено {success_count} из {len(words_to_update)} слов.")

if __name__ == "__main__":
    update_database()
