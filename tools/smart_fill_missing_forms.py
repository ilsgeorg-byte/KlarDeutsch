#!/usr/bin/env python3
"""
Умное заполнение отсутствующих форм через AI.
Скрипт сам определяет тип слова (существительное/глагол/прилагательное) и заполняет соответствующие поля.
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
import time

# === Настройки ===
BATCH_SIZE = 100  # Сколько слов обрабатывать за один запуск (оптимально 50-200)
DRY_RUN = False  # True = только просмотр, False = исправлять в БД
MAX_RETRIES = 3  # Максимум повторных попыток при ошибке API
RETRY_DELAY = 2  # Задержка между попытками (секунды)

# === Подключение к Groq ===
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("❌ GROQ_API_KEY не найден в .env.local")
    print("Получить ключ: https://console.groq.com/keys")
    sys.exit(1)

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
    timeout=30  # Увеличиваем таймаут
)

# Используем Qwen 3 32B - быстрее и стабильнее для пакетной обработки
# Альтернативы: 'llama-3.3-70b-versatile', 'mixtral-8x7b-32768', 'gemma2-9b-it'
MODEL_NAME = "qwen-3-32b"

# === Подключение к БД ===
def get_db_connection():
    url = os.environ.get("POSTGRES_URL")
    if not url:
        raise Exception("POSTGRES_URL не найдена")
    return psycopg2.connect(url)

# === Промпт для определения типа слова и заполнения форм ===
WORD_ANALYSIS_PROMPT = '''Ты - эксперт по немецкому языку. Определи тип слова и заполни соответствующие формы.

Слово: {de}
Перевод: {ru}
Текущий артикль: {article}
Текущие формы глагола: {verb_forms}
Текущее множественное число: {plural}

ЗАДАЧА:
1. Определи тип слова (noun/verb/adjective/phrase/other)
2. Заполни соответствующие формы:

Для СУЩЕСТВИТЕЛЬНЫХ (noun):
- corrected_article: der/die/das (обязательно)
- corrected_plural: форма множественного числа или "—" если нет мн.ч.
- corrected_verb_forms: "" (пустая строка)

Для ГЛАГОЛОВ (verb):
- corrected_article: "" (пустая строка)
- corrected_plural: "" (пустая строка)
- corrected_verb_forms: "Infinitiv, Präteritum, Partizip II"

Для ПРИЛАГАТЕЛЬНЫХ (adjective):
- corrected_article: "" (пустая строка)
- corrected_plural: "" (пустая строка)
- corrected_verb_forms: "" (пустая строка)

Для ФРАЗ и ДРУГИХ:
- Все поля пустые ""

Верни ТОЛЬКО JSON:
{{
  "word_type": "noun|verb|adjective|phrase|other",
  "corrected_article": "der/die/das или пустая строка",
  "corrected_plural": "форма мн.ч. или — или пустая строка",
  "corrected_verb_forms": "формы глагола или пустая строка",
  "confidence": 0.0-1.0,
  "explanation": "краткое объяснение"
}}

Примеры:
1. die Unterschrift = подпись
{{"word_type": "noun", "corrected_article": "die", "corrected_plural": "die Unterschriften", "corrected_verb_forms": "", "confidence": 1.0, "explanation": "существительное женского рода"}}

2. gehen = идти
{{"word_type": "verb", "corrected_article": "", "corrected_plural": "", "corrected_verb_forms": "gehen, ging, ist gegangen", "confidence": 1.0, "explanation": "неправильный глагол"}}

3. groß = большой
{{"word_type": "adjective", "corrected_article": "", "corrected_plural": "", "corrected_verb_forms": "", "confidence": 1.0, "explanation": "прилагательное"}}

4. neu = новый
{{"word_type": "adjective", "corrected_article": "", "corrected_plural": "", "corrected_verb_forms": "", "confidence": 1.0, "explanation": "прилагательное"}}

5. das Geld = деньги
{{"word_type": "noun", "corrected_article": "das", "corrected_plural": "—", "corrected_verb_forms": "", "confidence": 1.0, "explanation": "существительное среднего рода, не имеет множественного числа"}}
'''

def analyze_word_with_ai(de, ru, article, verb_forms, plural):
    """Определяет тип слова и заполняет формы через AI с повторными попытками"""
    for attempt in range(MAX_RETRIES):
        try:
            prompt = WORD_ANALYSIS_PROMPT.format(
                de=de,
                ru=ru or 'не указан',
                article=article or 'пусто',
                verb_forms=verb_forms or 'пусто',
                plural=plural or 'пусто'
            )
            
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "Ты - лингвистический эксперт. Возвращай только валидный JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content.strip()
            result = json.loads(content)
            return result, None
        except json.JSONDecodeError as e:
            # Ошибка парсинга JSON - не имеет смысла повторять
            return None, f"JSON ошибка: {e}. Ответ: {content[:100] if 'content' in locals() else ''}"
        except Exception as e:
            error_str = str(e)
            # Если это лимит API - ждём и повторяем
            if 'rate_limit' in error_str.lower() or '429' in error_str:
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY * (attempt + 1)
                    print(f"⏳ Лимит API, жду {wait_time}с...")
                    time.sleep(wait_time)
                    continue
                else:
                    return None, f"Превышен лимит API после {MAX_RETRIES} попыток"
            # Другие ошибки - повторяем
            elif attempt < MAX_RETRIES - 1:
                time.sleep(1)
                continue
            else:
                return None, error_str
    
    return None, "Превышено количество попыток"

def get_words_needing_fix(conn, limit=BATCH_SIZE):
    """Получает слова без plural или verb_forms"""
    cur = conn.cursor()
    
    # Все слова без plural ИЛИ без verb_forms
    cur.execute("""
        SELECT id, de, ru, article, verb_forms, plural
        FROM words
        WHERE (
            -- Существительные без plural (есть артикль)
            (article IS NOT NULL AND article != '' AND (plural IS NULL OR plural = ''))
            OR
            -- Слова без артикля и без verb_forms (могут быть глаголами или прилагательными)
            ((article IS NULL OR article = '') AND (verb_forms IS NULL OR verb_forms = ''))
        )
        ORDER BY ai_checked_at ASC NULLS FIRST
        LIMIT %s
    """, (limit,))
    
    words = []
    for row in cur.fetchall():
        words.append({
            'id': row[0],
            'de': row[1],
            'ru': row[2],
            'article': row[3],
            'verb_forms': row[4],
            'plural': row[5]
        })
    
    cur.close()
    return words

def main():
    print("=" * 60)
    print("Умное заполнение отсутствующих форм через AI")
    print(f"Модель: {MODEL_NAME}")
    print("=" * 60)
    
    if DRY_RUN:
        print("РЕЖИМ: ТОЛЬКО ПРОСМОТР (без исправлений)")
        print("Чтобы исправлять, установи DRY_RUN = False\n")
    else:
        print("РЕЖИМ: ИСПРАВЛЕНИЕ в БД")
        print(f"Пакет: {BATCH_SIZE} слов, макс. повторных попыток: {MAX_RETRIES}\n")
    
    conn = get_db_connection()
    words = get_words_needing_fix(conn, BATCH_SIZE)
    
    print(f"Найдено слов для проверки: {len(words)}\n")
    
    stats = {
        'total': 0,
        'nouns': 0,
        'nouns_fixed': 0,
        'verbs': 0,
        'verbs_fixed': 0,
        'adjectives': 0,
        'phrases': 0,
        'errors': 0,
        'retries': 0
    }
    
    start_time = time.time()
    
    for i, word in enumerate(words, 1):
        # Показываем прогресс каждые 10 слов
        if i % 10 == 0 or i == len(words):
            elapsed = time.time() - start_time
            avg_time = elapsed / i
            remaining = (len(words) - i) * avg_time
            print(f"\n⏱ Прогресс: {i}/{len(words)} ({i*100//len(words)}%), "
                  f"прошло: {elapsed:.0f}с, ост.: {remaining:.0f}с")
        
        result, error = analyze_word_with_ai(
            word['de'],
            word['ru'],
            word['article'],
            word['verb_forms'],
            word['plural']
        )
        
        if error:
            print(f"[{i}/{len(words)}] {word['de']} = {word['ru']}... ❌ Ошибка: {error[:60]}")
            stats['errors'] += 1
            if 'Лимит API' in error or 'повторных попыток' in error:
                stats['retries'] += 1
            continue
        
        word_type = result.get('word_type', 'unknown')
        stats['total'] += 1
        
        if word_type == 'noun':
            stats['nouns'] += 1
            article = result.get('corrected_article', '')
            plural = result.get('corrected_plural', '')
            
            print(f"[{i}/{len(words)}] {word['de']} = {word['ru']}... 📝 СУЩ: {article} {word['de']} → Pl: {plural or '(пусто)'}")
            
            if not DRY_RUN and (article or plural):
                updates = {}
                if article and article != word['article']:
                    updates['article'] = article
                if plural and plural != word['plural']:
                    updates['plural'] = plural
                
                if updates:
                    cur = conn.cursor()
                    fields = ', '.join([f"{k} = %s" for k in updates.keys()])
                    values = list(updates.values()) + [word['id']]
                    cur.execute(f"UPDATE words SET {fields} WHERE id = %s", values)
                    conn.commit()
                    cur.close()
                    stats['nouns_fixed'] += 1
        
        elif word_type == 'verb':
            stats['verbs'] += 1
            verb_forms = result.get('corrected_verb_forms', '')
            
            print(f"[{i}/{len(words)}] {word['de']} = {word['ru']}... 🔤 ГЛАГ: {word['de']} → {verb_forms or '(пусто)'}")
            
            if not DRY_RUN and verb_forms:
                cur = conn.cursor()
                cur.execute("UPDATE words SET verb_forms = %s WHERE id = %s", (verb_forms, word['id']))
                conn.commit()
                cur.close()
                stats['verbs_fixed'] += 1
        
        elif word_type == 'adjective':
            stats['adjectives'] += 1
            print(f"[{i}/{len(words)}] {word['de']} = {word['ru']}... 🎨 ПРИЛ: {word['de']} (пропуск, формы не нужны)")
        
        elif word_type in ['phrase', 'other']:
            stats['phrases'] += 1
            print(f"[{i}/{len(words)}] {word['de']} = {word['ru']}... 💬 ФРАЗА/ДРУГОЕ: {word['de']} (пропуск)")
        
        else:
            print(f"[{i}/{len(words)}] {word['de']} = {word['ru']}... ❓ Неизвестный тип: {word_type}")
            stats['errors'] += 1
    
    # Итоги
    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print("ИТОГИ:")
    print(f"  Всего обработано: {stats['total']}")
    print(f"  Существительных: {stats['nouns']} (исправлено: {stats['nouns_fixed']})")
    print(f"  Глаголов: {stats['verbs']} (исправлено: {stats['verbs_fixed']})")
    print(f"  Прилагательных: {stats['adjectives']}")
    print(f"  Фраз/другого: {stats['phrases']}")
    print(f"  Ошибок: {stats['errors']} (из них лимит: {stats['retries']})")
    print(f"  Время: {elapsed:.0f}с ({elapsed/60:.1f} мин)")
    if stats['total'] > 0:
        print(f"  Скорость: {stats['total']/elapsed:.1f} слов/сек")
    print("=" * 60)
    
    if DRY_RUN:
        print("\nЧтобы исправить формы, установи DRY_RUN = False в скрипте")
    else:
        print(f"\nДля обработки следующей партии просто запусти скрипт снова")
        print(f"Он возьмёт следующие {BATCH_SIZE} слов из очереди")
    
    conn.close()
    print("\n✅ Проверка завершена!")

if __name__ == "__main__":
    main()
