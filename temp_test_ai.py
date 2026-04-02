
import os, sys, json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env.local'))

client = OpenAI(api_key=os.environ.get("GROQ_API_KEY"), base_url="https://api.groq.com/openai/v1")

PROMPT_TEMPLATE = """Ты - эксперт по немецкому языку. Обогати слово данными для учебного приложения.

Слово: {de}
Текущий перевод: {ru}
Артикль: {article}

ЗАДАЧА:
1. ПЕРЕВОД (ru): Если у слова есть несколько важных значений, укажи их через запятую.
2. ТЕМА (topic): Определи наиболее подходящую тему (напр. "Еда", "Путешествия", "Работа", "Здоровье", "Общее").
3. ПРИМЕРЫ (examples): Создай МИНИМУМ 3 качественных, естественных предложения с этим словом + перевод.
4. Множественное число: Обязательно добавь для существительных, если нет.
5. ГЛАГОЛЫ: 4 формы через запятую.
6. СИНОНИМЫ/АНТОНИМЫ: Найди по 2-3 наиболее употребимых.
7. КОЛЛОКАЦИИ: Найди 3 наиболее частотных устойчивых сочетания.

Верни ТОЛЬКО JSON:
{{
  "de": "{de}",
  "ru": "перевод",
  "topic": "Тема",
  "article": "der|die|das|",
  "verb_forms": "forms",
  "plural": "plural",
  "examples": [
    {{"de": "...", "ru": "..."}},
    {{"de": "...", "ru": "..."}},
    {{"de": "...", "ru": "..."}}
  ],
  "synonyms": "син1, син2",
  "antonyms": "ант1, ант2",
  "collocations": "колл1, колл2, колл3"
}}
"""

test_words = [
    {"de": "widersprechen", "ru": "widersprechen", "article": ""},
    {"de": "die Duplizität", "ru": "двуличность", "article": "die"},
    {"de": "residieren", "ru": "резидировать", "article": ""}
]

results = []
for w in test_words:
    prompt = PROMPT_TEMPLATE.format(de=w['de'], ru=w['ru'], article=w['article'])
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        response_format={"type": "json_object"}
    )
    results.append(json.loads(resp.choices[0].message.content))

print(json.dumps(results, ensure_ascii=False, indent=2))
