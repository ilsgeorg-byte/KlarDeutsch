#!/usr/bin/env python3
"""
Скрипт для массового добавления отсутствующих форм множественного числа и форм глаголов.
Заполняет пробелы в данных через AI.
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
BATCH_SIZE = 50  # Сколько слов обрабатывать за один запуск
DRY_RUN = False  # True = только просмотр, False = исправлять в БД

# === Подключение к Groq ===
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

MODEL_NAME = "llama-3.3-70b-versatile"

# === Подключение к БД ===
def get_db_connection():
    url = os.environ.get("POSTGRES_URL")
    if not url:
        raise Exception("POSTGRES_URL не найдена")
    return psycopg2.connect(url)

# === Промпт для существительных без plural ===
NOUN_PLURAL_PROMPT = '''Ты - эксперт по немецкому языку. Дай форму множественного числа для существительного.

Слово: {de}
Артикль: {article}

Верни ТОЛЬКО JSON:
{{
  "plural": "форма множественного числа или — если нет",
  "confidence": 0.0-1.0
}}

Примеры:
- die Unterschrift -> {{"plural": "die Unterschriften", "confidence": 1.0}}
- das Geld -> {{"plural": "—", "confidence": 1.0}} (нет множественного числа)
- der Vater -> {{"plural": "die Väter", "confidence": 1.0}}
'''

# === Промпт для глаголов без verb_forms ===
VERB_FORMS_PROMPT = '''Ты - эксперт по немецкому языку. Дай формы глагола.

Глагол: {de}

Верни ТОЛЬКО JSON:
{{
  "verb_forms": "Infinitiv, Präteritum, Partizip II",
  "confidence": 0.0-1.0
}}

Примеры:
- gehen -> {{"verb_forms": "gehen, ging, ist gegangen", "confidence": 1.0}}
- essen -> {{"verb_forms": "essen, aß, hat gegessen", "confidence": 1.0}}
- machen -> {{"verb_forms": "machen, machte, hat gemacht", "confidence": 1.0}}
'''

def get_plural_from_ai(de, article):
    """Получает форму множественного числа через AI"""
    try:
        prompt = NOUN_PLURAL_PROMPT.format(de=de, article=article or 'не указан')
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Ты - лингвистический эксперт. Возвращай только валидный JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=200,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content.strip()
        result = json.loads(content)
        return result.get('plural'), None
    except Exception as e:
        return None, str(e)

def get_verb_forms_from_ai(de):
    """Получает формы глагола через AI"""
    try:
        prompt = VERB_FORMS_PROMPT.format(de=de)
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Ты - лингвистический эксперт. Возвращай только валидный JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=200,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content.strip()
        result = json.loads(content)
        return result.get('verb_forms'), None
    except Exception as e:
        return None, str(e)

def get_words_needing_fix(conn, limit=BATCH_SIZE):
    """Получает слова без plural или verb_forms"""
    cur = conn.cursor()
    
    # Существительные без plural (есть артикль, но нет множественного числа)
    cur.execute("""
        SELECT id, de, article, 'noun' as word_type, plural, verb_forms
        FROM words
        WHERE article IS NOT NULL AND article != ''
          AND (plural IS NULL OR plural = '')
          AND (verb_forms IS NULL OR verb_forms = '')
        ORDER BY ai_checked_at ASC NULLS FIRST
        LIMIT %s
    """, (limit,))
    
    nouns = []
    for row in cur.fetchall():
        nouns.append({
            'id': row[0],
            'de': row[1],
            'article': row[2],
            'word_type': row[3],
            'plural': row[4],
            'verb_forms': row[5]
        })
    
    # Глаголы без verb_forms (нет артикля, нет plural, но и нет forms - значит это глагол)
    # Прилагательные: нет article, нет verb_forms, нет plural - их пропускаем
    # Глаголы: нет article, есть verb_forms (пустой) - это глагол
    cur.execute("""
        SELECT id, de, article, 'verb' as word_type, plural, verb_forms, ru
        FROM words
        WHERE (article IS NULL OR article = '')
          AND (verb_forms IS NULL OR verb_forms = '')
          AND (plural IS NULL OR plural = '')
          AND (
            ru LIKE '%(гл%)%' OR
            ru LIKE '%глагол%' OR
            ru LIKE '%делать%' OR
            ru LIKE '%быть%' OR
            ru LIKE '%иметь%' OR
            ru LIKE '%мочь%' OR
            LOWER(de) IN ('sein', 'haben', 'werden', 'können', 'müssen', 'sollen', 'wollen', 'dürfen', 'mögen', 'machen', 'gehen', 'kommen', 'sehen', 'geben', 'wissen', 'finden', 'denken', 'nehmen', 'tun', 'lassen', 'stehen', 'liegen', 'sitzen', 'fahren', 'laufen', 'sprechen', 'lesen', 'schreiben', 'lernen', 'lehren', 'arbeiten', 'spielen', 'wohnen', 'leben', 'fragen', 'antworten', 'zeigen', 'bringen', 'holen', 'kaufen', 'verkaufen', 'essen', 'trinken', 'schlafen', 'aufstehen', 'anziehen', 'ausziehen', 'waschen', 'kochen', 'öffnen', 'schließen', 'beginnen', 'enden', 'warten', 'hören', 'riechen', 'fühlen', 'schmecken', 'verstehen', 'erklären', 'beschreiben', 'erzählen', 'diskutieren', 'vergessen', 'erinnern', 'wiederholen', 'üben', 'prüfen', 'gewinnen', 'verlieren', 'helfen', 'danken', 'bitten', 'grüßen', 'empfehlen', 'verbieten', 'versprechen', 'gefallen', 'gehören', 'passen', 'stimmen', 'bedeuten', 'erkennen', 'unterscheiden', 'vergleichen', 'wählen', 'wechseln', 'bewegen', 'entscheiden', 'entwickeln', 'entstehen', 'erreichen', 'erwarten', 'erzählen', 'feiern', 'fordern', 'fördern', 'führen', 'gelten', 'genügen', 'geschehen', 'gewinnen', 'glauben', 'handeln', 'halten', 'heben', 'kennen', 'klappen', 'kriegen', 'leiden', 'leihen', 'lernen', 'meinen', 'messen', 'nutzen', 'nützen', 'pflegen', 'raten', 'rechnen', 'retten', 'rufen', 'sammeln', 'schaffen', 'scheinen', 'schieben', 'schlagen', 'schließen', 'schneiden', 'schützen', 'schwimmen', 'senden', 'setzen', 'singen', 'sinken', 'sitzen', 'sparen', 'spazieren', 'spiegeln', 'spielen', 'sprechen', 'springen', 'stehen', 'stehlen', 'steigen', 'stellen', 'sterben', 'tragen', 'treffen', 'treiben', 'trennen', 'treten', 'trinken', 'tun', 'überleben', 'überzeugen', 'umziehen', 'verbinden', 'verbringen', 'verdienen', 'vereinen', 'vergleichen', 'verhaften', 'verhindern', 'verlangen', 'verlieren', 'vermeiden', 'veröffentlichen', 'verraten', 'verschwinden', 'versuchen', 'verteidigen', 'vertrauen', 'verwenden', 'wachsen', 'wählen', 'waschen', 'wechseln', 'werben', 'werden', 'werfen', 'wiederholen', 'wirken', 'wissen', 'wohnen', 'wollen', 'zeigen', 'ziehen', 'zwingen')
          )
        ORDER BY ai_checked_at ASC NULLS FIRST
        LIMIT %s
    """, (limit,))
    
    verbs = []
    for row in cur.fetchall():
        # Пропускаем прилагательные (они обычно имеют перевод типа "большой", "новый")
        # Проверяем по наличию глагольных маркеров в ru
        ru_lower = (row[6] or '').lower()
        # Если перевод содержит глагольные маркеры - это глагол
        is_verb = any(marker in ru_lower for marker in [
            '(гл', 'глагол', 'делать', 'быть', 'иметь', 'мочь', 'являться', 'казаться',
            'становиться', 'начинать', 'кончать', 'продолжать', 'пытаться', 'стараться'
        ])
        
        # Или если слово в списке распространённых глаголов
        common_verbs = {
            'sein', 'haben', 'werden', 'können', 'müssen', 'sollen', 'wollen', 'dürfen', 'mögen',
            'machen', 'gehen', 'kommen', 'sehen', 'geben', 'wissen', 'finden', 'denken', 'nehmen',
            'tun', 'lassen', 'stehen', 'liegen', 'sitzen', 'fahren', 'laufen', 'sprechen', 'lesen',
            'schreiben', 'lernen', 'arbeiten', 'spielen', 'wohnen', 'leben', 'fragen', 'antworten',
            'zeigen', 'bringen', 'holen', 'kaufen', 'essen', 'trinken', 'schlafen', 'waschen',
            'kochen', 'öffnen', 'schließen', 'beginnen', 'enden', 'warten', 'hören', 'verstehen',
            'erklären', 'beschreiben', 'erzählen', 'vergessen', 'erinnern', 'wiederholen', 'üben',
            'prüfen', 'gewinnen', 'verlieren', 'helfen', 'danken', 'bitten', 'empfehlen', 'versprechen',
            'gefallen', 'gehören', 'passen', 'stimmen', 'bedeuten', 'erkennen', 'wählen', 'wechseln',
            'bewegen', 'entscheiden', 'entwickeln', 'entstehen', 'erreichen', 'erwarten', 'feiern',
            'fordern', 'führen', 'gelten', 'genügen', 'geschehen', 'glauben', 'handeln', 'halten',
            'heben', 'kennen', 'kennenlernen', 'klappen', 'kriegen', 'leiden', 'leihen', 'meinen',
            'messen', 'nutzen', 'pflegen', 'raten', 'rechnen', 'retten', 'rufen', 'sammeln', 'schaffen',
            'scheinen', 'schieben', 'schlagen', 'schneiden', 'schützen', 'schwimmen', 'senden',
            'setzen', 'singen', 'sinken', 'sparen', 'spazieren', 'springen', 'stehlen', 'steigen',
            'stellen', 'sterben', 'tragen', 'treffen', 'treiben', 'trennen', 'treten', 'überleben',
            'überzeugen', 'umziehen', 'verbinden', 'verbringen', 'verdienen', 'vergleichen', 'verhaften',
            'verhindern', 'verlangen', 'vermeiden', 'veröffentlichen', 'verraten', 'verschwinden',
            'versuchen', 'verteidigen', 'vertrauen', 'verwenden', 'wachsen', 'werben', 'werfen',
            'wirken', 'zeigen', 'ziehen', 'zwingen', 'aufstehen', 'anziehen', 'ausziehen', 'einladen',
            'mitbringen', 'vorschlagen', 'zurückkommen', 'stattfinden', 'teilnehmen', 'fernsehen',
            'radfahren', 'schwimmengehen', 'spazierengehen', 'kennenlernen', 'dazulernen', 'weiterlernen'
        }
        
        if is_verb or row[1].lower() in common_verbs:
            verbs.append({
                'id': row[0],
                'de': row[1],
                'article': row[2],
                'word_type': row[3],
                'plural': row[4],
                'verb_forms': row[5]
            })
    
    cur.close()
    return nouns, verbs

def main():
    print("=" * 60)
    print("Заполнение отсутствующих форм множественного числа и глаголов")
    print("=" * 60)
    
    if DRY_RUN:
        print("РЕЖИМ: ТОЛЬКО ПРОСМОТР (без исправлений)")
        print("Чтобы исправлять, установи DRY_RUN = False\n")
    else:
        print("РЕЖИМ: ИСПРАВЛЕНИЕ в БД\n")
    
    conn = get_db_connection()
    nouns, verbs = get_words_needing_fix(conn, BATCH_SIZE)
    
    print(f"Найдено существительных без plural: {len(nouns)}")
    print(f"Найдено глаголов без verb_forms: {len(verbs)}")
    print()
    
    stats = {
        'nouns_processed': 0,
        'nouns_fixed': 0,
        'verbs_processed': 0,
        'verbs_fixed': 0,
        'errors': 0
    }
    
    # Обрабатываем существительные
    print("\n=== СУЩЕСТВИТЕЛЬНЫЕ (без plural) ===")
    for i, noun in enumerate(nouns, 1):
        print(f"[{i}/{len(nouns)}] {noun['article']} {noun['de']}...", end=" ")
        
        plural, error = get_plural_from_ai(noun['de'], noun['article'])
        
        if error:
            print(f"❌ Ошибка: {error[:50]}")
            stats['errors'] += 1
            continue
        
        if plural:
            if plural == '—':
                print(f"→ нет множественного числа (—)")
            else:
                print(f"→ {plural}")
            
            stats['nouns_processed'] += 1
            
            if not DRY_RUN:
                cur = conn.cursor()
                cur.execute("UPDATE words SET plural = %s WHERE id = %s", (plural, noun['id']))
                conn.commit()
                cur.close()
                stats['nouns_fixed'] += 1
        else:
            print(f"→ не удалось определить")
    
    # Обрабатываем глаголы
    print("\n=== ГЛАГОЛЫ (без verb_forms) ===")
    for i, verb in enumerate(verbs, 1):
        print(f"[{i}/{len(verbs)}] {verb['de']}...", end=" ")
        
        verb_forms, error = get_verb_forms_from_ai(verb['de'])
        
        if error:
            print(f"❌ Ошибка: {error[:50]}")
            stats['errors'] += 1
            continue
        
        if verb_forms:
            print(f"→ {verb_forms}")
            stats['verbs_processed'] += 1
            
            if not DRY_RUN:
                cur = conn.cursor()
                cur.execute("UPDATE words SET verb_forms = %s WHERE id = %s", (verb_forms, verb['id']))
                conn.commit()
                cur.close()
                stats['verbs_fixed'] += 1
        else:
            print(f"→ не удалось определить")
    
    # Итоги
    print("\n" + "=" * 60)
    print("ИТОГИ:")
    print(f"  Существительных обработано: {stats['nouns_processed']}")
    print(f"  Существительных исправлено: {stats['nouns_fixed']}")
    print(f"  Глаголов обработано: {stats['verbs_processed']}")
    print(f"  Глаголов исправлено: {stats['verbs_fixed']}")
    print(f"  Ошибок: {stats['errors']}")
    print("=" * 60)
    
    if DRY_RUN:
        print("\nЧтобы исправить формы, установи DRY_RUN = False в скрипте")
    
    conn.close()
    print("\n✅ Проверка завершена!")

if __name__ == "__main__":
    main()
