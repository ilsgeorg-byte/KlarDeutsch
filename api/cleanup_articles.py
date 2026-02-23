# cleanup_articles.py
# Запуск: python cleanup_articles.py

import json
from pathlib import Path

INPUT_FILE = Path("words.json")
OUTPUT_FILE = Path("words.cleaned.json")

# Какие значения topic считаем глаголами
VERB_TOPICS = {"Глаголы", "глаголы", "verbs"}


def is_verb(word: dict) -> bool:
    return str(word.get("topic", "")).strip() in VERB_TOPICS


def main():
    raw = INPUT_FILE.read_text(encoding="utf-8")
    data = json.loads(raw)

    if not isinstance(data, list):
        raise ValueError("Ожидался массив слов в words.json")

    cleaned = []
    for w in data:
        if is_verb(w) and "article" in w:
            w = {k: v for k, v in w.items() if k != "article"}
        cleaned.append(w)

    OUTPUT_FILE.write_text(json.dumps(cleaned, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Готово. Очищенный список записан в {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
