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
    print("❌ Ошибка: Убедись, что DATABASE_URL и GROQ_API_KEY есть в файле .env.local")
    exit(1)

groq_client = Groq(api_key=api_key)


def get_word_root(de_word):
    """Извлекаем корень слова и нормализуем умлауты для поиска."""
    word = de_word.strip()

    # Убираем артикли и служебные части
    for prefix in ["der ", "die ", "das ", "sich ", "Den ", "Die ", "Das "]:
        if word.startswith(prefix):
            word = word[len(prefix):]

    # Берём первое слово если словосочетание (например "ab und zu" → "ab")
    word = word.split()[0].lower()

    # Нормализуем умлауты — ищем и с умлаутом и без
    word = word.replace("ä", "a").replace("ö", "o").replace("ü", "u")

    return word

def normalize(text):
    """Нормализуем текст примера так же — убираем умлауты для сравнения."""
    return (text.lower()
            .replace("ä", "a").replace("ö", "o").replace("ü", "u")
            .replace("ß", "ss"))



def example_contains_word(example_de, de_word):
    """Проверяем наличие целевого слова с учётом умлаутов и словоформ."""
    root = get_word_root(de_word)
    example_normalized = normalize(example_de)
    return root in example_normalized


def get_linguistic_data_groq(de_word, level):
    prompt = f"""
Выведи строго JSON объект для немецкого слова "{de_word}" (уровень {level}).
Обязательные правила:
1. Каждый из 3 примеров ОБЯЗАН содержать именно слово "{de_word}" (или его грамматическую форму).
2. Не используй синонимы или другие слова вместо "{de_word}" в примерах.
3. Перевод — краткий, 1-3 слова.
4. Никаких лишних слов, только JSON:

{{
  "ru_translation": "Точный перевод на русский язык (1-3 слова)",
  "synonyms": "2 синонима через запятую, или пустая строка",
  "antonyms": "1 антоним, или пустая строка",
  "collocations": "2 коротких словосочетания с словом {de_word}",
  "examples": [
    {{"de": "Пример 1 с словом {de_word} или его формой.", "ru": "Перевод 1."}},
    {{"de": "Пример 2 с словом {de_word} или его формой.", "ru": "Перевод 2."}},
    {{"de": "Пример 3 с словом {de_word} или его формой.", "ru": "Перевод 3."}}
  ]
}}
"""

    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )

        text = completion.choices[0].message.content

        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            text = match.group(0)

        return json.loads(text)

    except Exception as e:
        print(f"\n[!] Ошибка API для слова '{de_word}': {e}")
        return None


def filter_valid_examples(examples_list, de_word):
    """Оставляем только примеры, где реально есть целевое слово."""
    valid = []
    for ex in examples_list:
        if isinstance(ex, dict) and "de" in ex and "ru" in ex:
            if example_contains_word(ex["de"], de_word):
                valid.append(ex)
            else:
                print(f"\n  ⚠️  Пример отклонён (нет слова '{de_word}'): {ex['de']}")
    return valid


def update_database():
    print("Подключаюсь к базе данных...")
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(url)
        cur = conn.cursor()

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

            data = get_linguistic_data_groq(de, level)

            if not data:
                print("❌ Пропущено (ошибка генерации)")
                continue

            ru_translation = data.get("ru_translation", "Перевод не найден")
            synonyms = data.get("synonyms", "")
            antonyms = data.get("antonyms", "")
            collocations = data.get("collocations", "")

            # Фильтруем примеры — только те, где есть целевое слово
            examples_list = data.get("examples", [])
            valid_examples = filter_valid_examples(examples_list, de)

            # Если ни один пример не прошёл фильтр — пропускаем слово
            if not valid_examples:
                print(f"❌ Пропущено (ни один пример не содержит слово '{de}')")
                continue

            examples_json = json.dumps(valid_examples, ensure_ascii=False)

            if synonyms:
                synonyms = ", ".join([s.strip() for s in synonyms.split(",") if s.strip()])
            if antonyms:
                antonyms = ", ".join([s.strip() for s in antonyms.split(",") if s.strip()])
            if collocations:
                collocations = ", ".join([c.strip() for c in collocations.split(",") if c.strip()])

            cur.execute("""
                UPDATE words 
                SET ru = %s, synonyms = %s, antonyms = %s, collocations = %s, examples = %s::jsonb 
                WHERE id = %s;
            """, (ru_translation, synonyms, antonyms, collocations, examples_json, word_id))

            conn.commit()
            print("✅")

            time.sleep(2)

        print("\n🎉 Все слова успешно обновлены!")

    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
            print("Соединение с базой закрыто.")


if __name__ == "__main__":
    update_database()
