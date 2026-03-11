#!/usr/bin/env python3
"""
Специализированный скрипт для проверки и улучшения точности переводов
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

# === Промпт для проверки точности перевода ===
TRANSLATION_CHECK_PROMPT = '''Ты - эксперт по немецко-русскому переводу. Проверь точность перевода.

Немецкое слово: {de}
Текущий перевод: {current_translation}
Артикль: {article}
Формы глагола: {verb_forms}

Оцени точность перевода по следующим критериям:
1. Соответствие значения: перевод действительно отражает значение немецкого слова?
2. Контекст: перевод подходит для общего использования или имеет узкую специализацию?
3. Полные значения: если слово имеет несколько значений, все ли они учтены?
4. Техническая точность: особенно важно для терминов, профессиональной лексики
5. Языковые особенности: перевод учитывает особенности русского языка?

Примеры проблем:
- "Handy" - "ручной" (неправильно), правильно "мобильный телефон"
- "Bekleidung" - "одежда" (правильно), а не "покрытие"
- "Arbeit" - "работа" (правильно), а не "труд" (слишком обобщенно)

Верни ТОЛЬКО валидный JSON без markdown:
{{
  "accuracy_score": 0.0-1.0,
  "issues": [],
  "suggested_translation": "предложенный более точный перевод",
  "explanation": "объяснение, почему текущий перевод неточен или правилен",
  "context_notes": "дополнительная информация о контексте использования"
}}

Если перевод точный - accuracy_score = 1.0, suggested_translation = текущий перевод'''

def check_translation_accuracy_with_ai(de, current_translation, article, verb_forms):
    """Проверяет точность перевода через ИИ"""
    try:
        prompt = TRANSLATION_CHECK_PROMPT.format(
            de=de,
            current_translation=current_translation,
            article=article or "отсутствует",
            verb_forms=verb_forms or "отсутствуют"
        )
        
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Ты проверяешь точность перевода с немецкого на русский. Возвращай ТОЛЬКО JSON, без markdown и пояснений."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=600
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
            'accuracy_score': 0.5,
            'issues': ['Ошибка парсинга JSON'],
            'suggested_translation': current_translation,
            'explanation': 'Ошибка парсинга ответа ИИ, сохраняем текущий перевод',
            'context_notes': 'Не удалось получить оценку точности'
        }, f"JSON ошибка: {e}. Ответ ИИ: {content[:100]}"
    except Exception as e:
        return None, str(e)

def get_words_to_check(conn, limit=CHECK_LIMIT):
    """Получает слова для проверки точности перевода"""
    cur = conn.cursor()
    
    # Выбираем все слова для проверки перевода
    cur.execute("""
        SELECT id, de, ru, article, verb_forms
        FROM words
        ORDER BY id
        LIMIT %s
    """, (limit,))
    
    words = []
    for row in cur.fetchall():
        words.append({
            'id': row[0],
            'de': row[1],
            'ru': row[2],
            'article': row[3],
            'verb_forms': row[4]
        })
    
    cur.close()
    return words

def update_translation_in_db(conn, word_id, corrected_translation):
    """Обновляет перевод в БД"""
    cur = conn.cursor()
    cur.execute("""
        UPDATE words SET ru = %s
        WHERE id = %s
    """, (corrected_translation, word_id))
    conn.commit()
    cur.close()

def main():
    print("=" * 60)
    print("Проверка точности переводов")
    print("=" * 60)
    
    if DRY_RUN:
        print("РЕЖИМ: ТОЛЬКО ПРОВЕРКА (без исправлений)")
        print("Чтобы исправлять, установи DRY_RUN = False\n")
    else:
        print("РЕЖИМ: ИСПРАВЛЕНИЕ в БД\n")
    
    conn = get_db_connection()
    words = get_words_to_check(conn)
    
    print(f"Найдено слов для проверки: {len(words)}\n")
    
    # Статистика
    stats = {
        'total': 0,
        'high_accuracy': 0,  # точность > 0.8
        'medium_accuracy': 0,  # 0.5-0.8
        'low_accuracy': 0,  # < 0.5
        'updated_translations': 0
    }
    
    for i, word in enumerate(words, 1):
        # Показываем прогресс только каждые 10 слов
        if i % 10 == 0 or i == len(words):
            print(f"Проверено: {i}/{len(words)}...")
        
        result, error = check_translation_accuracy_with_ai(
            word['de'],
            word['ru'],
            word['article'],
            word['verb_forms']
        )
        
        if error:
            print(f"  Ошибка при проверке {word['de']}: {error}")
            continue
        
        stats['total'] += 1
        
        accuracy = result.get('accuracy_score', 0.5)
        
        # Классифицируем по точности
        if accuracy > 0.8:
            stats['high_accuracy'] += 1
        elif accuracy > 0.5:
            stats['medium_accuracy'] += 1
        else:
            stats['low_accuracy'] += 1
        
        # Если точность низкая, показываем и предлагаем исправление
        if accuracy <= 0.7:
            print(f"\n[{i}] {word['de']} = {word['ru']}")
            print(f"   Точность: {accuracy:.2f}")
            print(f"   Проблемы: {result.get('issues', [])}")
            print(f"   Предложенный перевод: {result['suggested_translation']}")
            print(f"   Объяснение: {result['explanation']}")
            if result.get('context_notes'):
                print(f"   Контекст: {result['context_notes']}")
            
            if not DRY_RUN and result.get('suggested_translation') != word['ru']:
                update_translation_in_db(conn, word['id'], result['suggested_translation'])
                print(f"   [ПЕРЕВОД ИСПРАВЛЕН в БД]")
                stats['updated_translations'] += 1
    
    # Итоги
    print("\n" + "=" * 60)
    print("ИТОГИ:")
    print(f"   Всего проверено: {stats['total']}")
    print(f"   Высокая точность (>0.8): {stats['high_accuracy']} ({stats['high_accuracy']/stats['total']*100:.1f}%)")
    print(f"   Средняя точность (0.5-0.8): {stats['medium_accuracy']} ({stats['medium_accuracy']/stats['total']*100:.1f}%)")
    print(f"   Низкая точность (<0.5): {stats['low_accuracy']} ({stats['low_accuracy']/stats['total']*100:.1f}%)")
    if not DRY_RUN:
        print(f"   Обновлено переводов: {stats['updated_translations']}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    if DRY_RUN:
        print("Чтобы исправить переводы, установи DRY_RUN = False в скрипте")
    print("Проверка завершена!")

if __name__ == "__main__":
    main()