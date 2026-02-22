import os
import json
import time
import re
import psycopg2
import traceback
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

IRREGULAR_FORMS = {
    "sein":     ["bin", "ist", "war", "sind", "seid", "gewes"],
    "haben":    ["hat", "hab", "hatt", "hätt"],
    "werden":   ["wird", "wurde", "würd", "worden"],
    "können":   ["kann", "konn", "könn", "konnt"],
    "dürfen":   ["darf", "durf", "dürf", "durft"],
    "müssen":   ["muss", "müss", "musst"],
    "wollen":   ["will", "woll", "wollt"],
    "sollen":   ["soll", "sollt"],
    "mögen":    ["mag", "mog", "möch", "mocht"],
    "wissen":   ["weiß", "wuss", "wiss"],
    "sehen":    ["sieht", "sieh", "sah"],
    "gehen":    ["geht", "ging"],
    "kommen":   ["kommt", "kam"],
    "nehmen":   ["nimmt", "nahm"],
    "geben":    ["gibt", "gab"],
    "lassen":   ["lässt", "lass", "ließ"],
    "fahren":   ["fährt", "fuhr"],
    "laufen":   ["läuft", "lief"],
    "essen":    ["isst", "aß"],
    "lesen":    ["liest", "las"],
    "gelten":   ["gilt", "galt"],
    "erweisen": ["erwies", "erwiesen"],
    "stehen":   ["steht", "stand", "standen"],
    "halten":   ["hält", "hielt"],
    "fallen":   ["fällt", "fiel"],
    "treffen":  ["trifft", "traf"],
    "helfen":   ["hilft", "half"],
    "finden":   ["findet", "fand"],
    "bringen":  ["bringt", "brachte"],
    "denken":   ["denkt", "dachte"],
    "sprechen": ["spricht", "sprach"],
    "schreiben":["schreibt", "schrieb"],
}

SEPARABLE_PREFIXES = [
    "ab", "an", "auf", "aus", "bei", "da", "durch", "ein", "fort",
    "her", "hin", "los", "mit", "nach", "vor", "weg", "weiter",
    "wieder", "zu", "zurück", "zusammen"
]


def normalize(text):
    return (text.lower()
            .replace("ä", "a").replace("ö", "o").replace("ü", "u")
            .replace("ß", "ss"))


def has_cyrillic(text):
    if not text:
        return False
    return bool(re.search(r'[а-яёА-ЯЁ]', text))


def get_separable_parts(de_word):
    word = de_word.strip()
    for prefix in ["der ", "die ", "das ", "sich "]:
        if word.lower().startswith(prefix):
            word = word[len(prefix):]
    word = word.split()[0].lower()
    word = normalize(word)
    for prefix in SEPARABLE_PREFIXES:
        if word.startswith(prefix) and len(word) > len(prefix) + 2:
            stem = word[len(prefix):]
            if len(stem) > 4:
                stem = stem[:-2]
            return prefix, stem
    return None, None


def get_word_root(de_word):
    word = de_word.strip()
    for prefix in ["der ", "die ", "das ", "sich "]:
        if word.lower().startswith(prefix):
            word = word[len(prefix):]
    word = word.split()[0].lower()
    word = normalize(word)
    if len(word) > 4:
        word = word[:-2]
    return word


def example_contains_word(example_de, de_word):
    def norm(text):
        return text.lower().replace("ä","a").replace("ö","o").replace("ü","u").replace("ß","ss")

    example_lower = example_de.lower()
    word_lower = de_word.lower()
    example_norm = norm(example_de)

    # 1. Прямое вхождение
    if word_lower in example_lower:
        return True

    # 2. Извлекаем главный глагол (убираем sich, als, zu)
    stop = {"sich", "als", "zu", "nicht"}
    parts = [p for p in word_lower.split() if p not in stop]
    main_verb = parts[0] if parts else word_lower

    # 3. Неправильные формы
    if main_verb in IRREGULAR_FORMS:
        for form in IRREGULAR_FORMS[main_verb]:
            if norm(form) in example_norm:
                return True

    # 4. Отделяемые глаголы (aussehen → sieht...aus)
    prefix, stem = get_separable_parts(main_verb)
    if prefix and stem:
        for inf, forms in IRREGULAR_FORMS.items():
            if norm(inf).startswith(stem):
                if prefix in example_lower:
                    for form in forms:
                        if norm(form) in example_norm:
                            return True
        if stem in example_norm and prefix in example_lower:
            return True

    # 5. Стемминг для правильных глаголов
    root = get_word_root(main_verb)
    if len(root) >= 4 and root in example_norm:
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


def filter_valid_examples(examples_list, de_word):
    valid = []
    fallback = []
    for ex in examples_list:
        if isinstance(ex, dict) and "de" in ex and "ru" in ex:
            if not example_is_german(ex["de"]):
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
    if not examples_are_diverse(examples_list):
        return False
    for ex in examples_list:
        if isinstance(ex, dict) and "de" in ex:
            if not example_contains_word(ex["de"], de_word):
                return False
            if not example_is_german(ex["de"]):
                return False
    return True


def get_linguistic_data_groq(de_word, level):
    prompt = f"""Выведи строго JSON объект для немецкого слова "{de_word}" (уровень {level}).
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
    {{"de": "Немецкий пример 1 с {de_word}.", "ru": "Русский перевод 1."}},
    {{"de": "Немецкий пример 2 с {de_word}.", "ru": "Русский перевод 2."}},
    {{"de": "Немецкий пример 3 с {de_word}.", "ru": "Русский перевод 3."}}
  ]
}}"""
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
            print("\n🚫 Дневной лимит токенов исчерпан.")
            exit(0)
        if "429" in error_str:
            time.sleep(60)
            return None
        return None


def update_database():
    conn = psycopg2.connect(url)
    cur = conn.cursor()

    cur.execute("SELECT id, de, level, examples, ru, synonyms, antonyms, collocations FROM words ORDER BY id ASC;")
    all_words = cur.fetchall()

    needs_update = []
    for row in all_words:
        word_id, de, level, examples_raw, ru, synonyms, antonyms, collocations = row
        if examples_raw is None or ru == "перевод в процессе":
            needs_update.append(row)
            continue
        try:
            examples_list = examples_raw if isinstance(examples_raw, list) else json.loads(examples_raw)
            if not word_data_is_valid(de, ru, synonyms, antonyms, collocations, examples_list):
                needs_update.append(row)
        except Exception:
            needs_update.append(row)

    print(f"Найдено слов для обновления: {len(needs_update)}")

    for i, row in enumerate(needs_update, 1):
        word_id, de, level, examples_raw, ru, synonyms, antonyms, collocations = row
        print(f"[{i}/{len(needs_update)}] Обрабатываю: {de}... ", end="", flush=True)

        try:
            data = get_linguistic_data_groq(de, level)
            if not data:
                print("❌ (нет данных от API)")
                continue

            ru_translation = data.get("ru_translation", "Перевод не найден")
            synonyms       = data.get("synonyms", "")
            antonyms       = data.get("antonyms", "")
            collocations   = data.get("collocations", "")
            examples_list  = data.get("examples", [])

            valid_examples = filter_valid_examples(examples_list, de)

            if len(valid_examples) < 3 or not examples_are_diverse(valid_examples):
                print(f"❌ (примеров: {len(valid_examples)}/3)")
                continue

            examples_json = json.dumps(valid_examples, ensure_ascii=False)
            cur.execute(
                "UPDATE words SET ru=%s, synonyms=%s, antonyms=%s, collocations=%s, examples=%s::jsonb WHERE id=%s;",
                (ru_translation, synonyms, antonyms, collocations, examples_json, word_id)
            )
            conn.commit()
            print("✅")
            time.sleep(2)

        except Exception as e:
            print(f"❌ {type(e).__name__}: {e}")
            traceback.print_exc()
            with open("update_words_errors.log", "a", encoding="utf-8") as f:
                f.write(f"{de}\t{type(e).__name__}: {e}\n")
            continue

    cur.close()
    conn.close()
    print("\n🎉 Готово!")


if __name__ == "__main__":
    update_database()
