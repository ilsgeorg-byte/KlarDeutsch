#!/usr/bin/env python3
"""
Специализированный скрипт для проверки и исправления форм глаголов
"""

import os
import sys
import json
import re
import io
from dotenv import load_dotenv

# Фикс для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Загружаем переменные окружения
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))

import psycopg2
from openai import OpenAI

# === Настройки ===
CHECK_LIMIT = 500
DRY_RUN = True  # True = только проверка, False = исправлять в БД

# === Подключение к Groq (бесплатно, быстро) ===
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("❌ GROQ_API_KEY не найден в .env.local")
    print("Получить ключ: https://console.groq.com/keys")
    sys.exit(1)

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
    timeout=15
)

# Модель для проверки
MODEL_NAME = "llama-3.3-70b-versatile"

# === Подключение к БД ===
def get_db_connection():
    url = os.environ.get("POSTGRES_URL")
    if not url:
        raise Exception("POSTGRES_URL не найдена")
    return psycopg2.connect(url)

# === Промпт для проверки форм глаголов ===
VERB_FORMS_CHECK_PROMPT = '''Ты - эксперт по немецкому языку. Проверь формы глагола.

Глагол: {verb}
Текущие формы: {current_forms}

Правильные формы глагола включают:
1. Infinitiv (основная форма): gehen, essen, lesen
2. Praeteritum (прошедшее время): ging, ass, las
3. Partizip II (причастие прошедшего времени): gegangen, gegessen, gelesen

Для неправильных глаголов формы могут отличаться:
- gehen - ging - ist gegangen
- essen - ass - hat gegessen
- lesen - las - hat gelesen
- fahren - fuhr - ist gefahren
- sehen - sah - hat gesehen

Правила образования Partizip II:
- Правильные глаголы: ge + основа + t (gemacht)
- Неправильные глаголы: изменяется гласный основы (gegangen, gegessen)
- Возвратные глаголы: sich + infinitiv + ge...t/ge...en (sich gewaschen)
- Глаголы с приставками (ab-, an-, auf-, etc.): приставка остается в начале (aufgemacht)

Проверь, правильно ли указаны формы глагола.
Если формы неверны, предложи правильные.

Верни ТОЛЬКО валидный JSON без markdown:
{{
  "valid": true/false,
  "errors": [],
  "corrected_forms": "правильные формы глагола в формате 'Infinitiv, Praeteritum, Partizip II'",
  "explanation": "объяснение, почему формы правильные или неправильные",
  "confidence": 0.0-1.0
}}

Если формы глагола правильные - valid = true, corrected_forms = текущие формы'''

def check_verb_forms_with_ai(verb, current_forms):
    """Проверяет формы глагола через ИИ"""
    try:
        prompt = VERB_FORMS_CHECK_PROMPT.format(
            verb=verb,
            current_forms=current_forms or "отсутствуют"
        )
        
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Ты проверяешь формы глаголов в немецком языке. Возвращай ТОЛЬКО JSON, без markdown и пояснений."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        content = response.choices[0].message.content.strip()
        
        # Убираем markdown обёртки
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
        
        # Пытаемся найти JSON внутри текста
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            content = json_match.group()
        
        result = json.loads(content)
        return result, None
        
    except json.JSONDecodeError as e:
        return {
            'valid': True,
            'errors': [],
            'corrected_forms': current_forms,
            'explanation': 'Ошибка парсинга JSON, сохраняем текущие формы',
            'confidence': 0.5
        }, f"JSON ошибка: {e}. Ответ ИИ: {content[:100]}"
    except Exception as e:
        return None, str(e)

def get_verbs_to_check(conn, limit=CHECK_LIMIT):
    """Получает глаголы для проверки форм"""
    cur = conn.cursor()
    
    # Выбираем глаголы (те, у которых нет артикля, но есть формы или тема указывает на глагол)
    cur.execute("""
        SELECT id, de, verb_forms
        FROM words
        WHERE (article IS NULL OR article = '')
          AND (verb_forms IS NOT NULL AND verb_forms != '')
        ORDER BY id
        LIMIT %s
    """, (limit,))
    
    verbs = []
    for row in cur.fetchall():
        verbs.append({
            'id': row[0],
            'de': row[1],
            'verb_forms': row[2]
        })
    
    cur.close()
    return verbs

def update_verb_forms_in_db(conn, word_id, corrected_forms):
    """Обновляет формы глагола в БД"""
    cur = conn.cursor()
    cur.execute("""
        UPDATE words SET verb_forms = %s
        WHERE id = %s
    """, (corrected_forms, word_id))
    conn.commit()
    cur.close()

def main():
    print("=" * 60)
    print("Проверка форм глаголов")
    print("=" * 60)
    
    if DRY_RUN:
        print("РЕЖИМ: ТОЛЬКО ПРОВЕРКА (без исправлений)")
        print("Чтобы исправлять, установи DRY_RUN = False\n")
    else:
        print("РЕЖИМ: ИСПРАВЛЕНИЕ в БД\n")
    
    conn = get_db_connection()
    verbs = get_verbs_to_check(conn)
    
    print(f"Найдено глаголов для проверки: {len(verbs)}\n")
    
    # Статистика
    stats = {
        'total': 0,
        'valid_forms': 0,
        'needs_correction': 0,
        'errors': []
    }
    
    for i, verb in enumerate(verbs, 1):
        # Показываем прогресс только каждые 10 слов
        if i % 10 == 0 or i == len(verbs):
            print(f"Проверено: {i}/{len(verbs)}...")
        
        result, error = check_verb_forms_with_ai(
            verb['de'],
            verb['verb_forms']
        )
        
        if error:
            print(f"  Ошибка при проверке {verb['de']}: {error}")
            continue
        
        stats['total'] += 1
        
        if result.get('valid'):
            # Формы правильные
            stats['valid_forms'] += 1
        else:
            # Найдены ошибки
            print(f"\n[{i}] {verb['de']}")
            print(f"   Текущие формы: {verb['verb_forms']}")
            print(f"   Исправленные: {result['corrected_forms']}")
            print(f"   Ошибки: {result['errors']}")
            print(f"   Объяснение: {result['explanation']}")
            
            if not DRY_RUN:
                update_verb_forms_in_db(conn, verb['id'], result['corrected_forms'])
                print(f"   [ИСПРАВЛЕНО в БД]")
            
            stats['needs_correction'] += 1
    
    # Итоги
    print("\n" + "=" * 60)
    print("ИТОГИ:")
    print(f"   Всего проверено: {stats['total']}")
    print(f"   С правильными формами: {stats['valid_forms']}")
    print(f"   Нуждаются в исправлении: {stats['needs_correction']}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    if DRY_RUN:
        print("Чтобы исправить формы, установи DRY_RUN = False в скрипте")
    print("Проверка завершена!")

if __name__ == "__main__":
    main()