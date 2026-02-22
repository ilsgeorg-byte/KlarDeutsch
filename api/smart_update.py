import os
import json
import time
import re
import psycopg2
from dotenv import load_dotenv
from groq import Groq

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.local')
load_dotenv(dotenv_path)

url = os.getenv("DATABASE_URL")
api_key = os.getenv("GROQ_API_KEY")

if not url or not api_key:
    print("❌ Ошибка: Нет DATABASE_URL или GROQ_API_KEY в .env.local")
    exit(1)

groq_client = Groq(api_key=api_key)

def get_db_connection():
    return psycopg2.connect(url)

def has_cyrillic(text):
    if not text:
        return False
    return bool(re.search(r'[а-яёА-ЯЁ]', str(text)))

def needs_fixing(row):
    # Распаковываем все нужные поля из SELECT
    word_id, de, examples_raw, ru, synonyms, antonyms, collocations, plural, verb_forms = row
    
    # 1. Проверка перевода
    if not ru or ru.strip() == "перевод в процессе" or ru.strip() == "":
        return True
        
    # 2. Проверка на кириллицу в немецких полях
    if has_cyrillic(synonyms) or has_cyrillic(antonyms) or has_cyrillic(collocations):
        return True

    # 3. УМНАЯ ПРОВЕРКА ФОРМ (ИСПРАВЛЕНО)
    # Если в базе None (NULL), значит ИИ еще ни разу не заполнял эти колонки для этого слова.
    # Если там пустая строка "", значит ИИ уже проверил слово и решил, что форм у него НЕТ (например, "Guten Tag").
    if plural is None and verb_forms is None:
        # Отправляем на проверку только те слова, у которых гипотетически могут быть формы
        if de[0].isupper() or de.endswith("en"): 
            return True 

    # 4. Проверка примеров
    if not examples_raw:
        return True
    try:
        ex_list = examples_raw if isinstance(examples_raw, list) else json.loads(examples_raw)
        if not isinstance(ex_list, list) or len(ex_list) < 3:
            return True
        for ex in ex_list:
            if not isinstance(ex, dict) or "de" not in ex or "ru" not in ex:
                return True
            if has_cyrillic(ex["de"]):
                return True
    except Exception:
        return True
        
    return False


def validate_and_fix_with_ai(de_word, current_data):
    prompt = f"""
Ты — редактор немецкого словаря.
Слово: "{de_word}"

Текущие данные:
{json.dumps(current_data, ensure_ascii=False, indent=2)}

ЗАДАЧА: Заполни/исправь поля JSON.
1. ru_translation: Точный перевод (1-3 слова).
2. article: Только если сущ: "der", "die" или "das". Иначе "".
3. plural: Только если сущ: мн.ч. (например "die Kinder"). Иначе "".
4. verb_forms: Только если глагол: 3 формы (например "geht, ging, ist gegangen"). Иначе "".
5. synonyms, antonyms, collocations: На немецком.
6. examples: Ровно 3 примера (de + ru).

Верни ТОЛЬКО JSON:
{{
  "ru_translation": "...",
  "article": "...",
  "plural": "...",
  "verb_forms": "...",
  "synonyms": "...",
  "antonyms": "...",
  "collocations": "...",
  "examples": [
    {{"de": "...", "ru": "..."}},
    {{"de": "...", "ru": "..."}},
    {{"de": "...", "ru": "..."}}
  ]
}}
"""
    try:
        completion = groq_client.chat.completions.create(
            model="qwen/qwen3-32b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=1500,
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "rate limit" in error_str.lower():
            print(" ⏳ Rate limit, жду 60 сек...", end="", flush=True)
            time.sleep(60)
            return "RETRY"
        print(f"  ⚠️ Ошибка AI: {e}")
        return None

def process_batch(limit=100):
    print("\n🚀 Скрипт запущен! Подключаюсь к базе...")
    conn = get_db_connection()
    cur = conn.cursor()

    print("🔍 Скачиваю слова...")
    # Запрашиваем правильные колонки
    cur.execute("SELECT id, de, examples, ru, synonyms, antonyms, collocations, plural, verb_forms FROM words ORDER BY id ASC;")
    all_words = cur.fetchall()
    
    words_to_fix = []
    for row in all_words:
        if needs_fixing(row):
            words_to_fix.append(row)
            if len(words_to_fix) >= limit:
                break

    print(f"⚠️ Найдено слов для обработки: {len(words_to_fix)}")

    for i, row in enumerate(words_to_fix, 1):
        word_id, de, examples_raw, ru, synonyms, antonyms, collocations, plural, verb_forms = row
        print(f"[{i}/{len(words_to_fix)}] {de}... ", end="", flush=True)

        current_examples = []
        if examples_raw:
            try:
                current_examples = examples_raw if isinstance(examples_raw, list) else json.loads(examples_raw)
            except:
                pass

        current_data = {
            "ru_translation": ru,
            "synonyms": synonyms,
            "antonyms": antonyms,
            "collocations": collocations,
            "plural": plural,
            "verb_forms": verb_forms,
            "examples": current_examples
        }

        while True:
            new_data = validate_and_fix_with_ai(de, current_data)
            if new_data == "RETRY":
                continue
            break

        if new_data and isinstance(new_data, dict) and "examples" in new_data:
            # Обновляем все поля
            cur.execute("""
                UPDATE words 
                SET ru = %s, synonyms = %s, antonyms = %s, collocations = %s, 
                    plural = %s, verb_forms = %s, article = %s, examples = %s::jsonb 
                WHERE id = %s
            """, (
                new_data.get("ru_translation", ""),
                new_data.get("synonyms", ""),
                new_data.get("antonyms", ""),
                new_data.get("collocations", ""),
                new_data.get("plural", ""),
                new_data.get("verb_forms", ""),
                new_data.get("article", ""),
                json.dumps(new_data.get("examples", []), ensure_ascii=False),
                word_id
            ))
            conn.commit()
            print("✅")
        else:
            print("❌")
            
        time.sleep(0.5)

    cur.close()
    conn.close()
    print("\n🎉 Готово!")

if __name__ == "__main__":
    process_batch(100)
