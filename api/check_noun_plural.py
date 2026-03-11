#!/usr/bin/env python3
"""
Специализированный скрипт для проверки и исправления форм множественного числа существительных
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
CHECK_LIMIT = 4000
DRY_RUN = False  # True = только проверка, False = исправлять в БД

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
MODEL_NAME = "qwen/qwen3-32b"

# === Подключение к БД ===
def get_db_connection():
    url = os.environ.get("POSTGRES_URL")
    if not url:
        raise Exception("POSTGRES_URL не найдена")
    return psycopg2.connect(url)

# === Промпт для проверки форм множественного числа ===
PLURAL_CHECK_PROMPT = '''Ты - эксперт по немецкому языку. Проверь форму множественного числа существительного.

Слово в единственном числе: {singular}
Артикль: {article}
Форма множественного числа: {plural}

Особое внимание удели следующим случаям:
1. Слова с окончанием -ie: Portemonnaie - die Portemonnaies
2. Слова с окончанием -e: Blume - die Blumen, Vater - die Vaeter
3. Слова с французским происхождением: Restaurant - die Restaurants
4. Слова с изменяющимся гласным: Fuss - die Fuesse, Maus - die Maeuse

Верни ТОЛЬКО валидный JSON без markdown:
{{
  "valid": true/false,
  "errors": [],
  "corrected_plural": "правильная форма множественного числа",
  "explanation": "объяснение, почему форма правильная или неправильная",
  "confidence": 0.0-1.0
}}

Если форма множественного числа правильная - valid = true, corrected_plural = текущая форма'''

def check_plural_with_ai(singular, article, plural):
    """Проверяет форму множественного числа через ИИ"""
    try:
        prompt = PLURAL_CHECK_PROMPT.format(
            singular=singular,
            article=article or "не указан",
            plural=plural or "отсутствует"
        )
        
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Ты проверяешь формы множественного числа существительных в немецком языке. Возвращай ТОЛЬКО JSON, без markdown и пояснений."},
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
            'corrected_plural': plural,
            'explanation': 'Ошибка парсинга JSON, сохраняем текущую форму',
            'confidence': 0.5
        }, f"JSON ошибка: {e}. Ответ ИИ: {content[:100]}"
    except Exception as e:
        return None, str(e)

def get_nouns_to_check(conn, limit=CHECK_LIMIT):
    """Получает существительные для проверки формы множественного числа"""
    cur = conn.cursor()
    
    # Выбираем существительные (те, у которых есть артикль) и которые не являются глаголами
    cur.execute("""
        SELECT id, de, article, plural
        FROM words
        WHERE article IS NOT NULL AND article != ''
          AND (plural IS NULL OR plural = '')
          AND (verb_forms IS NULL OR verb_forms = '')
        ORDER BY id
        LIMIT %s
    """, (limit,))
    
    nouns = []
    for row in cur.fetchall():
        nouns.append({
            'id': row[0],
            'de': row[1],
            'article': row[2],
            'plural': row[3]
        })
    
    cur.close()
    return nouns

def update_plural_in_db(conn, word_id, corrected_plural):
    """Обновляет форму множественного числа в БД"""
    cur = conn.cursor()
    cur.execute("""
        UPDATE words SET plural = %s
        WHERE id = %s
    """, (corrected_plural, word_id))
    conn.commit()
    cur.close()

def main():
    print("=" * 60)
    print("Проверка форм множественного числа существительных")
    print("=" * 60)
    
    if DRY_RUN:
        print("РЕЖИМ: ТОЛЬКО ПРОВЕРКА (без исправлений)")
        print("Чтобы исправлять, установи DRY_RUN = False\n")
    else:
        print("РЕЖИМ: ИСПРАВЛЕНИЕ в БД\n")
    
    conn = get_db_connection()
    nouns = get_nouns_to_check(conn)
    
    print(f"Найдено существительных для проверки: {len(nouns)}\n")
    
    # Статистика
    stats = {
        'total': 0,
        'with_plural': 0,
        'needs_correction': 0,
        'errors': []
    }
    
    for i, noun in enumerate(nouns, 1):
        # Показываем прогресс только каждые 10 слов
        if i % 10 == 0 or i == len(nouns):
            print(f"Проверено: {i}/{len(nouns)}...")
        
        result, error = check_plural_with_ai(
            noun['de'],
            noun['article'],
            noun['plural']
        )
        
        if error:
            print(f"  Ошибка при проверке {noun['de']}: {error}")
            continue
        
        stats['total'] += 1
        
        if result.get('valid'):
            # Форма правильная или отсутствует
            if noun['plural'] and noun['plural'] != result.get('corrected_plural'):
                print(f"\n[{i}] {noun['de']} (артикль: {noun['article']})")
                print(f"   Текущая форма: {noun['plural']}")
                print(f"   Исправленная: {result['corrected_plural']}")
                print(f"   Объяснение: {result['explanation']}")
                
                if not DRY_RUN:
                    update_plural_in_db(conn, noun['id'], result['corrected_plural'])
                    print(f"   [ИСПРАВЛЕНО в БД]")
                
                stats['needs_correction'] += 1
            else:
                stats['with_plural'] += 1
        else:
            # Найдены ошибки
            print(f"\n[{i}] {noun['de']} (артикль: {noun['article']})")
            print(f"   Текущая форма: {noun['plural'] or 'отсутствует'}")
            print(f"   Исправленная: {result['corrected_plural']}")
            print(f"   Ошибки: {result['errors']}")
            print(f"   Объяснение: {result['explanation']}")
            
            if not DRY_RUN:
                update_plural_in_db(conn, noun['id'], result['corrected_plural'])
                print(f"   [ИСПРАВЛЕНО в БД]")
            
            stats['needs_correction'] += 1
    
    # Итоги
    print("\n" + "=" * 60)
    print("ИТОГИ:")
    print(f"   Всего проверено: {stats['total']}")
    print(f"   Уже с формой: {stats['with_plural']}")
    print(f"   Нуждаются в исправлении: {stats['needs_correction']}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    if DRY_RUN:
        print("Чтобы исправить формы, установи DRY_RUN = False в скрипте")
    print("Проверка завершена!")

if __name__ == "__main__":
    main()