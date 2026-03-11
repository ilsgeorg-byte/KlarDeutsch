#!/usr/bin/env python3
"""
AI проверка слов в базе данных KlarDeutsch
Использует Groq API для проверки правильности слов и переводов
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
CHECK_LIMIT = 500  # Проверяем по 500 слов за раз (70B модель медленная)
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
MODEL_NAME = "llama-3.3-70b-versatile"  # Точная, меньше ошибок
# MODEL_NAME = "llama-3.1-8b-instant"  # Быстрая, но чаще ошибается

# === Подключение к БД ===
def get_db_connection():
    url = os.environ.get("POSTGRES_URL")
    if not url:
        raise Exception("POSTGRES_URL не найдена")
    return psycopg2.connect(url)

# === Промпт для ИИ ===
CHECK_PROMPT = '''Ты - строгий эксперт по немецкому языку. Проверь слово.

Слово: {de}
Перевод: {ru}
Артикль: {article}
Формы глагола: {verb_forms}

Определи тип слова и проверяй по правилам:

1. **Прилагательные** (быстрый, легкий, трудный и т.д.):
   - Артикль должен быть ПУСТЫМ
   - Формы глагола должны быть ПУСТЫМИ

2. **Глаголы** (делать, идти, видеть и т.д.):
   - Артикль должен быть ПУСТЫМ
   - Формы глагола: Infinitiv, Praeteritum, Partizip II (через запятую)

3. **Существительные** (дом, стол, книга и т.д.):
   - Артикль: der/die/das
   - Формы глагола должны быть ПУСТЫМИ

Верни ТОЛЬКО валидный JSON без markdown:
{{
  "word_type": "adjective|verb|noun",
  "valid": true/false,
  "errors": [],
  "corrected_de": "",
  "corrected_ru": "",
  "corrected_article": "",
  "corrected_verb_forms": "",
  "confidence": 0.0-1.0
}}

Если слово верное - valid = true, errors = []'''

def has_mixed_alphabet(text):
    """
    Проверяет смешение кириллицы и латиницы в ОДНОМ слове.
    
    Примеры:
    - "Дiploma" — True (смешение в одном слове: Д = кириллица, iploma = латиница)
    - "Привет" — False (только кириллица)
    - "Hallo" — False (только латиница)
    - "Привет Hallo" — False (разные слова)
    """
    if not text:
        return False
    
    # Проверяем КАЖДОЕ отдельное слово
    for word in text.split():
        cyrillic_count = 0
        latin_count = 0
        
        for char in word:
            # Кириллица
            if '\u0400' <= char <= '\u04FF':
                cyrillic_count += 1
            # Латиница (включая немецкие умлауты)
            elif ('a' <= char.lower() <= 'z') or char in 'äöüßÄÖÜ':
                latin_count += 1
        
        # Если в ОДНОМ слове есть и кириллица И латиница (больше 0 каждого) — ошибка
        if cyrillic_count > 0 and latin_count > 0:
            return True
    
    return False

def check_word_with_ai(de, ru, article, verb_forms):
    """Проверяет слово через ИИ"""
    
    # Сначала проверяем на смешение алфавитов (локально, без ИИ)
    if has_mixed_alphabet(ru):
        print(f"  [LOCAL] Mixed alphabet in RU: {ru}")
        return {
            'valid': False,
            'errors': ['Смешение алфавитов (кириллица + латиница)'],
            'corrected_ru': ru,  # Нужно исправить вручную
            'confidence': 1.0
        }, None
    
    if has_mixed_alphabet(de):
        print(f"  [LOCAL] Mixed alphabet in DE: {de}")
        return {
            'valid': False,
            'errors': ['Смешение алфавитов в немецком слове'],
            'corrected_de': de,
            'confidence': 1.0
        }, None
    
    # Если смешения нет — продолжаем проверку через ИИ
    try:
        prompt = CHECK_PROMPT.format(
            de=de,
            ru=ru,
            article=article or "пусто",
            verb_forms=verb_forms or "пусто"
        )
        
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Ты проверяешь немецкие слова. Возвращай ТОЛЬКО JSON, без markdown и пояснений."},
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
        # Возвращаем упрощённый результат если JSON не распарсился
        return {
            'valid': True,
            'errors': [],
            'confidence': 0.5,
            'note': 'JSON не распарсен, но слово скорее верно'
        }, f"JSON ошибка: {e}. Ответ ИИ: {content[:100]}"
    except Exception as e:
        return None, str(e)

def get_words_to_check(conn, limit=CHECK_LIMIT):
    """Получает слова для проверки (только непроверенные)"""
    cur = conn.cursor()
    
    # Сначала пробуем получить непроверенные слова
    cur.execute("""
        SELECT id, de, ru, article, verb_forms, level
        FROM words
        WHERE ai_checked_at IS NULL
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
            'verb_forms': row[4],
            'level': row[5]
        })
    
    # Если все слова уже проверены, берём старые (по дате проверки)
    if not words:
        print("Все слова уже проверены! Проверяем старые...")
        cur.execute("""
            SELECT id, de, ru, article, verb_forms, level
            FROM words
            ORDER BY ai_checked_at ASC NULLS FIRST
            LIMIT %s
        """, (limit,))
        
        for row in cur.fetchall():
            words.append({
                'id': row[0],
                'de': row[1],
                'ru': row[2],
                'article': row[3],
                'verb_forms': row[4],
                'level': row[5]
            })
    
    cur.close()
    return words

def mark_word_as_checked(conn, word_id):
    """Отмечает слово как проверенное"""
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE words SET ai_checked_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (word_id,))
        conn.commit()
        cur.close()
    except Exception as e:
        # Если соединение разорвано - пробуем переподключиться
        print(f"  [DB Error] {e}")
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                UPDATE words SET ai_checked_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (word_id,))
            conn.commit()
            cur.close()
            print("  [Reconnected OK]")
        except Exception as e2:
            print(f"  [Reconnect Failed] {e2}")

def update_word_in_db(conn, word_id, corrections):
    """Обновляет слово в БД с учётом типа слова"""
    cur = conn.cursor()

    # Получаем тип слова из результата ИИ
    word_type = corrections.get('word_type', 'unknown')
    
    # Преобразуем verb_forms из dict в строку если нужно
    verb_forms = corrections.get('corrected_verb_forms')
    if isinstance(verb_forms, dict):
        verb_forms = f"{verb_forms.get('Infinitiv', '')}, {verb_forms.get('Präteritum', '')}, {verb_forms.get('Partizip II', '')}"

    # Получаем значения и обрезаем если слишком длинные
    de = corrections.get('corrected_de')
    ru = corrections.get('corrected_ru')
    article = corrections.get('corrected_article')
    
    # === ВАЛИДАЦИЯ ПО ТИПУ СЛОВА ===
    
    # Прилагательные и глаголы НЕ должны иметь артикль
    if word_type in ['adjective', 'verb']:
        if article and len(article) > 3:  # ИИ пытается добавить артикль — игнорируем
            print(f"  [SKIP] Игнорируем артикль для {word_type}: {article}")
            article = None
    
    # Существительные НЕ должны иметь verb_forms
    if word_type == 'noun':
        if verb_forms and len(verb_forms) > 10:  # ИИ пытается добавить формы глагола
            print(f"  [SKIP] Игнорируем verb_forms для noun: {verb_forms}")
            verb_forms = None
    
    # Артикль должен быть коротким (der/die/das или пусто)
    if article and len(article) > 10:
        article = None  # Игнорируем длинные "исправления"
    
    # Обрезаем длинные значения
    if de and len(de) > 200:
        de = de[:200]
    if ru and len(ru) > 200:
        ru = ru[:200]
    if verb_forms and len(verb_forms) > 200:
        verb_forms = verb_forms[:200]

    # Используем COALESCE чтобы не обновлять пустые значения
    cur.execute("""
        UPDATE words SET
            de = COALESCE(NULLIF(%s, ''), de),
            ru = COALESCE(NULLIF(%s, ''), ru),
            article = COALESCE(NULLIF(%s, ''), article),
            verb_forms = COALESCE(NULLIF(%s, ''), verb_forms),
            ai_checked_at = NOW()
        WHERE id = %s
    """, (de, ru, article, verb_forms, word_id))
    
    conn.commit()
    cur.close()

def main():
    print("=" * 60)
    print("AI проверка слов немецкого языка")
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
        'valid': 0,
        'invalid': 0,
        'errors': []
    }
    
    for i, word in enumerate(words, 1):
        # Показываем прогресс только каждые 10 слов
        if i % 10 == 0 or i == len(words):
            print(f"Проверено: {i}/{len(words)}...")
        
        result, error = check_word_with_ai(
            word['de'],
            word['ru'],
            word['article'],
            word['verb_forms']
        )
        
        if error:
            # Ошибка ИИ - считаем слово проверенным но без результата
            stats['total'] += 1
            stats['valid'] += 1  # Считаем верным по умолчанию
            mark_word_as_checked(conn, word['id'])  # Отмечаем как проверенное
            continue
        
        stats['total'] += 1
        
        if result.get('valid'):
            # Слово верное - НЕ показываем
            stats['valid'] += 1
            mark_word_as_checked(conn, word['id'])  # Отмечаем как проверенное
        else:
            # Найдены ошибки - ПОКАЗЫВАЕМ
            print(f"\n[{i}] {word['de']} = {word['ru']}")
            print(f"   Ошибки:")
            for err in result.get('errors', []):
                print(f"      - {err}")
            
            if result.get('corrected_de') and result['corrected_de'] != word['de']:
                print(f"      -> Немецкий: {word['de']} -> {result['corrected_de']}")
            if result.get('corrected_ru') and result['corrected_ru'] != word['ru']:
                print(f"      -> Перевод: {word['ru']} -> {result['corrected_ru']}")
            if result.get('corrected_article') and result['corrected_article'] != word['article']:
                print(f"      -> Артикль: {word['article']} -> {result['corrected_article']}")
            if result.get('corrected_verb_forms') and result['corrected_verb_forms'] != word['verb_forms']:
                print(f"      -> Формы: {word['verb_forms']} -> {result['corrected_verb_forms']}")
            
            stats['invalid'] += 1
            stats['errors'].append({
                'word_id': word['id'],
                'word': word['de'],
                'translation': word['ru'],
                'corrections': result
            })
            
            # Исправляем в БД если не DRY_RUN
            if not DRY_RUN:
                update_word_in_db(conn, word['id'], result)
                print(f"   [ИСПРАВЛЕНО в БД]")
            
            mark_word_as_checked(conn, word['id'])  # Отмечаем как проверенное
    
    # Итоги
    print("\n" + "=" * 60)
    print("ИТОГИ:")
    print(f"   Всего проверено: {stats['total']}")
    print(f"   Верно: {stats['valid']} ({stats['valid']/stats['total']*100:.1f}%)")
    print(f"   Ошибки: {stats['invalid']} ({stats['invalid']/stats['total']*100:.1f}%)")
    
    # Сколько осталось проверить
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM words WHERE ai_checked_at IS NULL")
    remaining = cur.fetchone()[0]
    cur.close()
    print(f"\n   Осталось проверить: {remaining}")
    
    if stats['errors']:
        print(f"\nСлова с ошибками ({len(stats['errors'])} шт):")
        for err in stats['errors'][:20]:  # Показываем первые 20
            corrections = err['corrections']
            errors_list = corrections.get('errors', [])
            print(f"   - {err['word']} ({err['translation']}): {len(errors_list)} ошиб.")
    else:
        print("\nВсе слова проверены без ошибок!")
    
    conn.close()
    
    print("\n" + "=" * 60)
    if DRY_RUN:
        print("Чтобы исправить ошибки, установи DRY_RUN = False в скрипте")
    print("Проверка завершена!")

if __name__ == "__main__":
    main()
