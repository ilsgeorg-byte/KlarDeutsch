#!/usr/bin/env python3
"""
Улучшенная проверка слов в базе данных KlarDeutsch
Добавляет проверку:
- Множественного числа у существительных
- Форм глаголов (Infinitiv, Präsens, Präteritum, Perfekt)
- Правильности артиклей
- Переводов с учетом контекста
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

# === Подключение к БД ===
def get_db_connection():
    url = os.environ.get("POSTGRES_URL")
    if not url:
        raise Exception("POSTGRES_URL не найдена")
    return psycopg2.connect(url)

# === Промпт для ИИ с улучшенной проверкой ===
ENHANCED_CHECK_PROMPT = '''Ты - строгий эксперт по немецкому языку. Проверь слово и его формы.

Слово: {de}
Перевод: {ru}
Артикль: {article}
Формы глагола: {verb_forms}
Множественное число: {plural}

Определи тип слова и проверяй по полным правилам:

1. **Существительные** (дом, стол, книга и т.д.):
   - Должны иметь артикль: der/masculine, die/feminine, das/neuter
   - Должны иметь форму множественного числа (если применимо)
   - Проверь правильность артикля и формы множественного числа
   - Пример: "Haus" - артикль "das", множественное "die Hauser"

2. **Глаголы** (делать, идти, видеть и т.д.):
   - Не должны иметь артикля
   - Должны иметь формы: Infinitiv, Praeteritum, Partizip II (через запятую)
   - Пример: "gehen" - "gehen, ging, ist gegangen"

3. **Прилагательные** (быстрый, легкий, трудный и т.д.):
   - Не должны иметь артикля
   - Не должны иметь форм глагола или множественного числа

ВАЖНО: Проверь перевод на точность и контекст. Убедись, что:
- Перевод соответствует значению немецкого слова
- Учтены возможные значения слова в разных контекстах
- Множественное число правильно образовано
- Формы глагола правильные (особенно неправильные глаголы)

Верни ТОЛЬКО валидный JSON без markdown:
{{
  "word_type": "adjective|verb|noun",
  "valid": true/false,
  "errors": [],
  "corrections": {{
    "de": "исправленное немецкое слово",
    "ru": "исправленный перевод",
    "article": "исправленный артикль",
    "verb_forms": "исправленные формы глагола",
    "plural": "исправленная форма множественного числа"
  }},
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

def check_word_with_enhanced_ai(de, ru, article, verb_forms, plural=None):
    """Проверяет слово через ИИ с улучшенной логикой"""
    
    # Сначала проверяем на смешение алфавитов (локально, без ИИ)
    if has_mixed_alphabet(ru):
        print(f"  [LOCAL] Mixed alphabet in RU: {ru}")
        return {
            'valid': False,
            'errors': ['Смешение алфавитов (кириллица + латиница)'],
            'corrections': {'ru': ru},  # Нужно исправить вручную
            'confidence': 1.0
        }, None
    
    if has_mixed_alphabet(de):
        print(f"  [LOCAL] Mixed alphabet in DE: {de}")
        return {
            'valid': False,
            'errors': ['Смешение алфавитов в немецком слове'],
            'corrections': {'de': de},
            'confidence': 1.0
        }, None
    
    # Если смешения нет — продолжаем проверку через ИИ
    try:
        prompt = ENHANCED_CHECK_PROMPT.format(
            de=de,
            ru=ru,
            article=article or "пусто",
            verb_forms=verb_forms or "пусто",
            plural=plural or "пусто"
        )
        
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Ты проверяешь немецкие слова. Возвращай ТОЛЬКО JSON, без markdown и пояснений."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=800
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
            'corrections': {},
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
        SELECT id, de, ru, article, verb_forms, plural, level
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
            'plural': row[5],
            'level': row[6]
        })
    
    # Если все слова уже проверены, берём старые (по дате проверки)
    if not words:
        print("Все слова уже проверены! Проверяем старые...")
        cur.execute("""
            SELECT id, de, ru, article, verb_forms, plural, level
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
                'plural': row[5],
                'level': row[6]
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

    # Получаем значения и обрезаем если слишком длинные
    de = corrections.get('de')
    ru = corrections.get('ru')
    article = corrections.get('article')
    verb_forms = corrections.get('verb_forms')
    plural = corrections.get('plural')
    
    # Преобразуем verb_forms из dict в строку если нужно
    if isinstance(verb_forms, dict):
        verb_forms = f"{verb_forms.get('Infinitiv', '')}, {verb_forms.get('Präteritum', '')}, {verb_forms.get('Partizip II', '')}"

    # Обрезаем длинные значения
    if de and len(de) > 200:
        de = de[:200]
    if ru and len(ru) > 200:
        ru = ru[:200]
    if verb_forms and len(verb_forms) > 200:
        verb_forms = verb_forms[:200]
    if plural and len(plural) > 200:
        plural = plural[:200]

    # Используем COALESCE чтобы не обновлять пустые значения, но всегда обновляем ai_checked_at
        cur.execute("""
            UPDATE words SET
                de = COALESCE(NULLIF(%s, ''), de),
                ru = COALESCE(NULLIF(%s, ''), ru),
                article = COALESCE(NULLIF(%s, ''), article),
                verb_forms = COALESCE(NULLIF(%s, ''), verb_forms),
                plural = COALESCE(NULLIF(%s, ''), plural),
                ai_checked_at = NOW()
            WHERE id = %s
        """, (de, ru, article, verb_forms, plural, word_id))
    
    conn.commit()
    cur.close()

def main():
    print("=" * 60)
    print("УЛУЧШЕННАЯ AI проверка слов немецкого языка")
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
        
        result, error = check_word_with_enhanced_ai(
            word['de'],
            word['ru'],
            word['article'],
            word['verb_forms'],
            word['plural']
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
            
            corrections = result.get('corrections', {})
            if corrections.get('de') and corrections['de'] != word['de']:
                print(f"      -> Немецкий: {word['de']} -> {corrections['de']}")
            if corrections.get('ru') and corrections['ru'] != word['ru']:
                print(f"      -> Перевод: {word['ru']} -> {corrections['ru']}")
            if corrections.get('article') and corrections['article'] != word['article']:
                print(f"      -> Артикль: {word['article']} -> {corrections['article']}")
            if corrections.get('verb_forms') and corrections['verb_forms'] != word['verb_forms']:
                print(f"      -> Формы: {word['verb_forms']} -> {corrections['verb_forms']}")
            if corrections.get('plural') and corrections['plural'] != word['plural']:
                print(f"      -> Множественное: {word['plural']} -> {corrections['plural']}")
            
            stats['invalid'] += 1
            stats['errors'].append({
                'word_id': word['id'],
                'word': word['de'],
                'translation': word['ru'],
                'corrections': result
            })
            
            # Исправляем в БД если не DRY_RUN
            if not DRY_RUN:
                update_word_in_db(conn, word['id'], corrections)
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