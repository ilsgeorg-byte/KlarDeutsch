import os
import json
import time
import re
import psycopg2
from dotenv import load_dotenv
from groq import Groq

# Загружаем переменные из .env.local
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.local')
load_dotenv(dotenv_path)

# Достаем ключи
url = os.getenv("DATABASE_URL")
api_key = os.getenv("GROQ_API_KEY")

if not url or not api_key:
    print("❌ Ошибка: Убедись, что DATABASE_URL и GROQ_API_KEY есть в файле .env.local")
    exit(1)

# Инициализируем клиент Groq
groq_client = Groq(api_key=api_key)

def get_linguistic_data_groq(de_word, level):
    prompt = f"""
    Выведи строго JSON объект для немецкого слова "{de_word}" (уровень {level}).
    Обязательно дай русский перевод этого слова. Пиши кратко. Никаких лишних слов, только этот JSON:
    {{
      "ru_translation": "Точный перевод на русский язык (1-3 слова)",
      "synonyms": "2 синонима через запятую, или пустая строка",
      "antonyms": "1 антоним, или пустая строка",
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
            # Если Llama спотыкается, можно поменять на gemma2-9b-it
            model="llama-3.1-8b-instant", 
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        text = completion.choices[0].message.content
        
        # На всякий случай вырезаем всё лишнее до первой и после последней фигурной скобки
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            text = match.group(0)
            
        return json.loads(text)
        
    except Exception as e:
        print(f"\n[!] Ошибка API для слова '{de_word}': {e}")
        return None

def update_database():
    print("Подключаюсь к базе данных...")
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(url)
        cur = conn.cursor()
        
        # Ищем слова, у которых нет примеров ИЛИ перевод стоит как "перевод в процессе"
        cur.execute("""
            SELECT id, de, level 
            FROM words 
            WHERE examples IS NULL OR ru = 'перевод в процессе' 
            ORDER BY id ASC;
        """)
        words_to_update = cur.fetchall()
        
        total = len(words_to_update)
        print(f"Найдено слов для обновления: {total}\n")
        
        for i, row in enumerate(words_to_update, 1):
            word_id = row[0]
            de = row[1]
            level = row[2]
            
            print(f"[{i}/{total}] Обрабатываю: {de}...", end=" ", flush=True)
            
            # Запрашиваем данные у нейросети
            data = get_linguistic_data_groq(de, level)
            
            if not data:
                print("❌ Пропущено (ошибка генерации)")
                continue
                
            # Достаем данные из JSON ответа
            ru_translation = data.get("ru_translation", "Перевод не найден")
            synonyms = data.get("synonyms", "")
            antonyms = data.get("antonyms", "")
            collocations = data.get("collocations", "")
            
            # Преобразуем массив примеров в JSON строку для базы
            examples_list = data.get("examples", [])
            examples_json = json.dumps(examples_list, ensure_ascii=False)
            
            # Чистим пробелы после запятых (чтобы на фронтенде не слипались)
            if synonyms: synonyms = ", ".join([s.strip() for s in synonyms.split(",") if s.strip()])
            if antonyms: antonyms = ", ".join([s.strip() for s in antonyms.split(",") if s.strip()])
            if collocations: collocations = ", ".join([c.strip() for c in collocations.split(",") if c.strip()])

            # Сохраняем все данные, включая русский перевод
            cur.execute("""
                UPDATE words 
                SET ru = %s, synonyms = %s, antonyms = %s, collocations = %s, examples = %s::jsonb 
                WHERE id = %s;
            """, (ru_translation, synonyms, antonyms, collocations, examples_json, word_id))
            
            conn.commit()
            print("✅")
            
            # Пауза, чтобы не превысить лимиты API (Rate Limit)
            time.sleep(2)
            
        print("\n🎉 Все слова успешно обновлены!")
            
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        if conn: conn.rollback()
    finally:
        if cur: cur.close()
        if conn:
            conn.close()
            print("Соединение с базой закрыто.")

if __name__ == "__main__":
    update_database()
