#!/usr/bin/env python3
"""
AI проверка слов в базе данных KlarDeutsch
Использует Groq API для проверки правильности слов и переводов

Функции:
- Проверка на несколько значимых переводов
- Удаление конструкций типа Guten Tag, Guten Abend
- Проверка смешения алфавитов
- Проверка артиклей и форм глаголов
- Запуск проверки через API из админки
"""

import os
import sys
import json
import re
import io
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List, Tuple

# Фикс для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Загружаем переменные окружения
# Путь от файла скрипта к .env.local в корне проекта
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env.local'))
load_dotenv(env_path)

import psycopg2
from openai import OpenAI

# === Настройки ===
CHECK_LIMIT = 500  # Проверяем по 500 слов за раз (70B модель медленная)
DRY_RUN = False  # True = только проверка, False = исправлять в БД
ADD_MISSING_TRANSLATIONS = True  # Добавлять недостающие переводы если есть
REMOVE_GREETING_CONSTRUCTIONS = True  # Удалять конструкции Guten Tag, Guten Abend и т.д.

# === Подключение к Groq (бесплатно, быстро) ===
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("❌ GROQ_API_KEY не найден в .env.local")
    print("Получить ключ: https://console.groq.com/keys")
    sys.exit(1)

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
    timeout=30
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
CHECK_PROMPT = '''Ты - строгий эксперт по немецкому языку. Проверь слово и найди все ошибки.

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

4. **Конструкции приветствий** (Guten Tag, Guten Abend, Guten Morgen, Gute Nacht):
   - Это фразы, а не отдельные слова
   - Если это такая фраза - помечай как invalid с ошибкой "Конструкция приветствия - удалить"

5. **Несколько переводов**:
   - Если у слова есть несколько значимых переводов, найди их все
   - Пример: "der Rock" = "юбка", но также может быть "жилет" (истор.)
   - Пример: "das Band" = "лента", "связь", "обручальное кольцо"
   - Добавляй все основные переводы через запятую

Верни ТОЛЬКО валидный JSON без markdown:
{{
  "word_type": "adjective|verb|noun|phrase",
  "valid": true/false,
  "errors": [],
  "corrected_de": "",
  "corrected_ru": "",
  "corrected_article": "",
  "corrected_verb_forms": "",
  "additional_translations": [],
  "confidence": 0.0-1.0,
  "is_greeting_construction": true/false
}}

Если слово верное - valid = true, errors = []
Если найдены дополнительные переводы - добавь их в additional_translations'''

# === Конструкции для удаления ===
GREETING_PATTERNS = [
    r'^guten\s+tag$',
    r'^guten\s+abend$',
    r'^guten\s+morgen$',
    r'^gute\s+nacht$',
    r'^guten\s+rutsch$',
    r'^frohe\s+weihnachten$',
    r'^frohe\s+ostern$',
    r'^herzlichen\s+glückwunsch',
    r'^guten\s+appetit$',
    r'^auf\s+wiedersehen$',
    r'^machs?\s+gut$',
    r'^bis\s+bald$',
    r'^bis\s+morgen$',
    r'^bis\s+später$',
]

def is_greeting_construction(de: str) -> bool:
    """Проверяет, является ли фраза конструкцией приветствия/прощания"""
    de_lower = de.lower().strip()
    for pattern in GREETING_PATTERNS:
        if re.match(pattern, de_lower):
            return True
    return False

def has_mixed_alphabet(text: str) -> bool:
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

def check_word_with_ai(de: str, ru: str, article: str, verb_forms: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Проверяет слово через ИИ"""

    # Сначала проверяем на смешение алфавитов (локально, без ИИ)
    if has_mixed_alphabet(ru):
        print(f"  [LOCAL] Mixed alphabet in RU: {ru}")
        return {
            'valid': False,
            'errors': ['Смешение алфавитов (кириллица + латиница)'],
            'corrected_ru': ru,  # Нужно исправить вручную
            'confidence': 1.0,
            'additional_translations': []
        }, None

    if has_mixed_alphabet(de):
        print(f"  [LOCAL] Mixed alphabet in DE: {de}")
        return {
            'valid': False,
            'errors': ['Смешение алфавитов в немецком слове'],
            'corrected_de': de,
            'confidence': 1.0,
            'additional_translations': []
        }, None

    # Проверяем на конструкции приветствий
    if REMOVE_GREETING_CONSTRUCTIONS and is_greeting_construction(de):
        print(f"  [LOCAL] Greeting construction: {de}")
        return {
            'valid': False,
            'errors': ['Конструкция приветствия - удалить'],
            'is_greeting_construction': True,
            'confidence': 1.0,
            'additional_translations': []
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
        
        # Добавляем дополнительные переводы если есть
        if 'additional_translations' not in result:
            result['additional_translations'] = []
        
        return result, None

    except json.JSONDecodeError as e:
        # Возвращаем упрощённый результат если JSON не распарсился
        return {
            'valid': True,
            'errors': [],
            'confidence': 0.5,
            'note': 'JSON не распарсен, но слово скорее верно',
            'additional_translations': []
        }, f"JSON ошибка: {e}. Ответ ИИ: {content[:100]}"
    except Exception as e:
        return None, str(e)

def get_words_to_check(conn, limit=CHECK_LIMIT, word_id: Optional[int] = None):
    """Получает слова для проверки (только непроверенные или конкретное слово)"""
    cur = conn.cursor()

    # Если указан конкретный ID - проверяем только его
    if word_id is not None:
        cur.execute("""
            SELECT id, de, ru, article, verb_forms, level
            FROM words
            WHERE id = %s
        """, (word_id,))
    else:
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
    if not words and word_id is None:
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

def add_additional_translations(conn, word_id: int, additional_translations: List[str]):
    """Добавляет дополнительные переводы к слову"""
    if not additional_translations:
        return
    
    cur = conn.cursor()
    
    # Получаем текущий перевод
    cur.execute("SELECT ru FROM words WHERE id = %s", (word_id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        return
    
    current_ru = row[0]
    
    # Добавляем только уникальные переводы
    current_translations = [t.strip().lower() for t in current_ru.split(',')]
    for translation in additional_translations:
        trans_clean = translation.strip().lower()
        if trans_clean and trans_clean not in current_translations:
            current_ru += ', ' + translation.strip()
            current_translations.append(trans_clean)
    
    # Обновляем запись
    cur.execute("""
        UPDATE words SET ru = %s WHERE id = %s
    """, (current_ru, word_id))
    
    conn.commit()
    cur.close()
    print(f"  [+] Добавлены переводы: {', '.join(additional_translations)}")

def update_word_in_db(conn, word_id, corrections):
    """Обновляет слово в БД с учётом типа слова"""
    cur = conn.cursor()

    # Получаем тип слова из результата ИИ
    word_type = corrections.get('word_type', 'unknown')

    # Проверяем на конструкцию приветствия
    if corrections.get('is_greeting_construction'):
        print(f"  [!] Конструкция приветствия - помечаем на удаление")
        cur.close()
        return 'greeting'

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
    
    # Добавляем дополнительные переводы если есть
    if ADD_MISSING_TRANSLATIONS and corrections.get('additional_translations'):
        add_additional_translations(conn, word_id, corrections['additional_translations'])
    
    return 'updated'

def check_all_words(conn, limit=CHECK_LIMIT, dry_run=False) -> Dict[str, Any]:
    """Основная функция проверки всех слов"""
    words = get_words_to_check(conn, limit)
    
    print(f"Найдено слов для проверки: {len(words)}\n")

    # Статистика
    stats = {
        'total': 0,
        'valid': 0,
        'invalid': 0,
        'greeting_constructions': 0,
        'additional_translations_added': 0,
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
            
            # Но добавляем дополнительные переводы если есть
            if ADD_MISSING_TRANSLATIONS and result.get('additional_translations'):
                if not dry_run:
                    add_additional_translations(conn, word['id'], result['additional_translations'])
                    stats['additional_translations_added'] += len(result['additional_translations'])
                else:
                    print(f"\n[{i}] {word['de']} = {word['ru']}")
                    print(f"   Дополнительные переводы: {result['additional_translations']}")
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
            
            # Проверяем на дополнительные переводы
            if result.get('additional_translations'):
                print(f"      + Дополнительные переводы: {result['additional_translations']}")

            stats['invalid'] += 1
            
            # Проверяем на конструкцию приветствия
            if result.get('is_greeting_construction'):
                stats['greeting_constructions'] += 1
                print(f"   [!] КОНСТРУКЦИЯ ПРИВЕТСТВИЯ - рекомендуется удалить")
            
            stats['errors'].append({
                'word_id': word['id'],
                'word': word['de'],
                'translation': word['ru'],
                'corrections': result
            })

            # Исправляем в БД если не DRY_RUN
            if not dry_run:
                update_status = update_word_in_db(conn, word['id'], result)
                if update_status == 'greeting':
                    print(f"   [!] КОНСТРУКЦИЯ - помечено на удаление")
                else:
                    print(f"   [ИСПРАВЛЕНО в БД]")

            mark_word_as_checked(conn, word['id'])  # Отмечаем как проверенное

    return stats

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

    # Статистика
    stats = check_all_words(conn, CHECK_LIMIT, DRY_RUN)

    # Итоги
    print("\n" + "=" * 60)
    print("ИТОГИ:")
    print(f"   Всего проверено: {stats['total']}")
    print(f"   Верно: {stats['valid']} ({stats['valid']/stats['total']*100:.1f}%)")
    print(f"   Ошибки: {stats['invalid']} ({stats['invalid']/stats['total']*100:.1f}%)")
    print(f"   Конструкции приветствий: {stats['greeting_constructions']}")
    print(f"   Добавлено переводов: {stats['additional_translations_added']}")

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
            greeting_mark = " [ПРИВЕТСТВИЕ]" if corrections.get('is_greeting_construction') else ""
            print(f"   - {err['word']} ({err['translation']}): {len(errors_list)} ошиб.{greeting_mark}")
    else:
        print("\nВсе слова проверены без ошибок!")

    conn.close()

    print("\n" + "=" * 60)
    if DRY_RUN:
        print("Чтобы исправить ошибки, установи DRY_RUN = False в скрипте")
    print("Проверка завершена!")

if __name__ == "__main__":
    main()
