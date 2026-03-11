#!/usr/bin/env python3
"""
Шаг 2: Проверить слова через AI
Читает words_to_check.json, сохраняет results.json
"""

import os, sys, json, re
if sys.platform == 'win32':
    sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))

from openai import OpenAI

# Client с таймаутом
client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
    timeout=15
)

# Промпт
PROMPT = """
Ты — строгий эксперт по немецкому языку. Проверь слово.

Слово: {de}
Перевод: {ru}
Артикль: {article}
Формы: {verb_forms}
Пример: {example_de} — {example_ru}

Верни ТОЛЬКО JSON:
{{
  "valid": true/false,
  "errors": [],
  "corrected_de": "",
  "corrected_ru": "",
  "corrected_article": "",
  "corrected_verb_forms": "",
  "corrected_example_de": "",
  "corrected_example_ru": ""
}}
"""

print("AI Check - words_to_check.json\n")
print("=" * 50)

# Читаем слова
with open('words_to_check.json', 'r', encoding='utf-8') as f:
    words = json.load(f)

print(f"Checking {len(words)} words...\n")

results = []
for i, w in enumerate(words, 1):
    print(f"[{i}/{len(words)}] {w['de']}...", end=" ")
    
    try:
        prompt = PROMPT.format(
            de=w['de'],
            ru=w['ru'],
            article=w['article'] or '-',
            verb_forms=w['verb_forms'] or '-',
            example_de=w['example_de'] or '-',
            example_ru=w['example_ru'] or '-'
        )
        
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=500
        )
        
        content = resp.choices[0].message.content.strip()
        
        # Чистим JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        
        result = json.loads(content)
        result['id'] = w['id']  # Добавляем ID
        
        if result.get('valid'):
            print("OK")
        else:
            print(f"ERRORS: {len(result.get('errors', []))}")
        
        results.append(result)
        
    except Exception as e:
        print(f"ERR: {str(e)[:40]}")
        results.append({'id': w['id'], 'error': str(e)})

# Сохраняем результаты
with open('results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 50)
print(f"✅ Saved {len(results)} results to results.json")

# Статистика
valid = sum(1 for r in results if r.get('valid'))
errors = len(results) - valid
print(f"   Valid: {valid}, Errors: {errors}")
