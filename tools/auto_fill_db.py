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

SEPARABLE_PREFIXES = [
    "ab", "an", "auf", "aus", "bei", "da", "durch", "ein", "fort",
    "her", "hin", "los", "mit", "nach", "vor", "weg", "weiter",
    "wieder", "zu", "zurück", "zusammen"
]


def get_phrase_keywords(de_word):
    """
    Для составных выражений типа 'gelten als', 'es gibt', 'Angst haben vor'
    возвращает список ключевых слов, все из которых должны быть в примере.
    Для обычных слов возвращает пустой список.
    """
    parts = de_word.strip().lower().split()
    if len(parts) >= 2:
        stopwords = {"der", "die", "das", "sich", "den", "dem", "ein", "eine"}
        keywords = [p for p in parts if p not in stopwords]
        return keywords
    return []


def normalize(text):
    return (text.lower()
            .replace("ä", "a").replace("ö", "o").replace("ü", "u")
            .replace("ß", "ss"))


def has_cyrillic(text):
    if not text:
        return False
    return bool(re.search(r'[а-яёА-ЯЁ]', text))


def get_separable_parts(de_word):
    """
    Для отделяемых глаголов возвращает (приставка, основа).
    Например: ausgehen → ('aus', 'geh')
    Если не отделяемый — возвращает (None, None).
    """
    word = de_word.strip()
    for prefix in ["der ", "die ", "das ", "sich ", "Den ", "Die ", "Das "]:
        if word.startswith(prefix):
            word = word[len(prefix):]
    word = word.split()[0].lower()
    word = word.replace("ä", "a").replace("ö", "o").replace("ü", "u").replace("ß", "ss")

    for prefix in SEPARABLE_PREFIXES:
        if word.startswith(prefix) and len(word) > len(prefix) + 2:
            stem = word[len(prefix):]
            if len(stem) > 4:
                stem = stem[:-2]
            return prefix, stem

    return None, None


def get_word_root(de_word):
    word = de_word.strip()
    for prefix in ["der ", "die ", "das ", "sich ", "Den ", "Die ", "Das "]:
        if word.startswith(prefix):
            word = word[len(prefix):]
    word = word.split()[0].lower()
    word = word.replace("ä", "a").replace("ö", "o").replace("ü", "u").replace("ß", "ss")
    if len(word) > 4:
        word = word[:-2]
    return word


def example_contains_word(example_de, de_word):
    example_norm = normalize(example_de)

    # 1. Проверка составных выражений (gelten als, es gibt, Angst haben vor...)
    keywords = get_phrase_keywords(de_word)
    if keywords:
        norm_keywords = [normalize(k) for k in keywords]
        if all(kw in example_norm for kw in norm_keywords):
            return True

    # 2. Обычный поиск по корню
    root = get_word_root(de_word)
    if root in example_norm:
        return True

    # 3. Проверка отделяемого глагола
    prefix, stem = get_separable_parts(de_word)
    if prefix and stem:
        if prefix in example_norm and stem in example_norm:
            return True

    return False


def example_is_german(example_de):
    return not has_cyrillic(example_de)


def examples_are_diverse(examples_list):
    if len(examples_list) < 2:
        return True
    texts = [normalize(ex.get("de", "")) for ex in examples_list]
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            words_i = set(texts[i].split())
            words_j = set(texts[j].split())
            if not words_i or not words_j:
                continue
            similarity = len(words_i & words_j) / min(len(words_i), len(words_j))
            if similarity > 0.6:
                return False
    return True


def examples_are_valid(examples_list, de_word):
    if not examples_list:
        return False
    for ex in examples_list:
        if isinstance(ex, dict) and "de" in ex:
            if not example_contains_word(ex["de"], de_word):
                return False
            if not example_is_german(ex["de"]):
                return False
    if not examples_are_diverse(examples_list):
        return False
    return True


def word_data_is_valid(de_word, ru, synonyms, antonyms, collocations, examples_list):
    if not ru or ru == "перевод в процессе":
        return False
    if has_cyrillic(synonyms):
        return False
    if has_cyrillic(antonyms):
        return False
    if has_cyrillic(collocations):
        return False
    if not examples_list or len(examples_list) < 3:
        return False
    if not examples_are_valid(examples_list, de_word):
        return False
    return True


def get_linguistic_data_groq(de_word, level):
    prompt = f"""
Выведи строго JSON объект для немецкого слова "{de_word}" (уровень {level}).
Обязательные правила:
1. Каждый из 3 примеров ОБЯЗАН содержать именно слово "{de_word}" (или его грамматическую форму).
2. Не используй синонимы или другие слова вместо "{de_word}" в примерах.
3. Поле "de" в примерах — ТОЛЬКО на немецком языке. Никакого русского в поле "de".
4. Поле "ru" в примерах — ТОЛЬКО перевод на русском языке.
5. Все 3 примера должны быть разными по смыслу и структуре.
6. synonyms, antonyms, collocations — ТОЛЬКО на немецком языке, никакого русского.
7. Перевод — краткий, 1-3 слова на русском.
8. Никаких лишних слов, только JSON:

{{
  "ru_translation": "Точный перевод на русский язык (1-3 слова)",
  "synonyms": "2 синонима на немецком через запятую, или пустая строка",
  "antonyms": "1 антоним на немецком, или пустая строка",
  "collocations": "2 коротких словосочетания на немецком с словом {de_word}",
  "examples": [
    {{"de": "Немецкий пример 1 с {de_word} — одна ситуация.", "ru": "Русский перевод 1."}},
    {{"de": "Немецкий пример 2 с {de_word} — другая ситуация.", "ru": "Русский перевод 2."}},
    {{"de": "Немецкий пример 3 с {de_word} — третья ситуация.", "ru": "Русский перевод 3."}}
  ]
}}
"""
    try:
        completion = groq_client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        text = completion.choices[0].message.content
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            text = match.group(0)
        return json.loads(text)

    except Exception as e:
        error_str = str(e)
        if "tokens per day" in error_str or "TPD" in error_str:
            print(f"\n🚫 Дневной лимит токенов исчерпан. Запусти скрипт завтра.")
            print(f"   Остановлено на слове: '{de_word}'")
            exit(0)
        if "429" in error_str:
            print(f"\n⏳ Rate limit, жду 60 секунд...")
            time.sleep(60)
            return None
        print(f"\n[!] Ошибка API для слова '{de_word}': {e}")
        return None


def filter_valid_examples(examples_list, de_word):
    valid = []
    fallback = []

    for ex in examples_list:
        if isinstance(ex, dict) and "de" in ex and "ru" in ex:
            if not example_is_german(ex["de"]):
                print(f"\n  ⚠️  Пример отклонён (не немецкий): {ex['de']}")
                continue
            if not example_contains_word(ex["de"], de_word):
                print(f"\n  ⚠️  Пример отклонён (нет слова '{de_word}'): {ex['de']}")
                fallback.append(ex)
                continue
            valid.append(ex)

    if not valid and fallback:
        print(f"\n  ⚠️  Используем fallback примеры для '{de_word}'")
        return fallback

    return valid


def update_database():
    print("Подключаюсь к базе данных...")
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(url)
        cur = conn.cursor()

        cur.execute("""
            SELECT id, de, level, examples, ru, synonyms, antonyms, collocations
            FROM words
            ORDER BY id ASC;
        """)
        all_words = cur.fetchall()

        total = len(all_words)
        print(f"Всего слов в базе: {total}\n")

        needs_update = []

        print("Проверяю все поля на корректность...")
        for row in all_words:
            word_id, de, level, examples_raw, ru, synonyms, antonyms, collocations = row

            # Незаполненные — сразу в очередь
            if examples_raw is None or ru == "перевод в процессе":
                needs_update.append(row)
                continue

            # Заполненные — полная проверка всех полей
            try:
                examples_list = (examples_raw
                                 if isinstance(examples_raw, list)
                                 else json.loads(examples_raw))
                if not word_data_is_valid(de, ru, synonyms, antonyms,
                                          collocations, examples_list):
                    print(f"  ⚠️  Требует исправления: {de}")
                    needs_update.append(row)
            except Exception:
                needs_update.append(row)

        print(f"\nНайдено слов для обновления/исправления: {len(needs_update)}\n")

        for i, row in enumerate(needs_update, 1):
            word_id, de, level = row[0], row[1], row[2]

            print(f"[{i}/{len(needs_update)}] Обрабатываю: {de}...", end=" ", flush=True)

            data = get_linguistic_data_groq(de, level)

            if not data:
                print("❌ Пропущено (ошибка генерации)")
                continue

            ru_translation = data.get("ru_translation", "Перевод не найден")
            synonyms = data.get("synonyms", "")
            antonyms = data.get("antonyms", "")
            collocations = data.get("collocations", "")

            if has_cyrillic(synonyms):
                print(f"\n  ⚠️  Синонимы на русском, очищаю: {synonyms}")
                synonyms = ""
            if has_cyrillic(antonyms):
                print(f"\n  ⚠️  Антоним на русском, очищаю: {antonyms}")
                antonyms = ""
            if has_cyrillic(collocations):
                print(f"\n  ⚠️  Связки на русском, очищаю: {collocations}")
                collocations = ""

            examples_list = data.get("examples", [])
            valid_examples = filter_valid_examples(examples_list, de)

            if not valid_examples:
                print(f"❌ Пропущено (нет валидных примеров для '{de}')")
                continue

            if len(valid_examples) < 3:
                print(f"❌ Пропущено (недостаточно примеров: {len(valid_examples)} из 3)")
                continue

            if not examples_are_diverse(valid_examples):
                print(f"❌ Пропущено (примеры слишком похожи для '{de}')")
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

        print("\n🎉 Готово! Все слова проверены и обновлены.")

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

