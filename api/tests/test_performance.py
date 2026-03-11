#!/usr/bin/env python3
"""
Тест производительности SQL-запросов KlarDeutsch
Сравнивает время выполнения запросов до/после оптимизации
"""

import os
import sys
import time
import io
from dotenv import load_dotenv

# Фикс для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))

import psycopg2

def get_connection():
    url = os.environ.get("POSTGRES_URL")
    if not url:
        raise Exception("POSTGRES_URL не найдена")
    return psycopg2.connect(url)

def measure_query(cur, query, params=(), description="Запрос"):
    """Измеряет время выполнения запроса"""
    start = time.perf_counter()
    # Поддержка именованных параметров (dict) и позиционных (tuple)
    if isinstance(params, dict):
        cur.execute(query, params)
    else:
        cur.execute(query, params)
    _ = cur.fetchall()
    elapsed = (time.perf_counter() - start) * 1000  # мс
    print(f"  {description}: {elapsed:.2f} мс")
    return elapsed

def main():
    print("=" * 60)
    print("🚀 Тест производительности SQL-запросов")
    print("=" * 60)
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Получаем тестового пользователя
    cur.execute("SELECT id FROM users ORDER BY id LIMIT 1")
    user = cur.fetchone()
    if not user:
        print("❌ Нет пользователей в БД")
        return 1
    
    user_id = user[0]
    print(f"\n📊 Тестирование для пользователя ID: {user_id}")
    
    # Получаем размеры таблиц
    cur.execute("""
        SELECT relname, n_live_tup 
        FROM pg_stat_user_tables 
        WHERE schemaname = 'public'
        ORDER BY n_live_tup DESC
    """)
    print("\n📈 Размер таблиц:")
    for row in cur.fetchall():
        print(f"   {row[0]}: {row[1]:,} строк")
    
    results = {}
    
    # ============================================================
    # Тест 1: Trainer API - выборка слов для тренировки
    # ============================================================
    print("\n" + "=" * 60)
    print("1️⃣  Trainer API - выборка слов для тренировки")
    print("=" * 60)
    
    queries_trainer = [
        ("Новые слова (LEFT JOIN)", """
            SELECT w.id, w.level, w.topic, w.de, w.ru
            FROM words w
            LEFT JOIN user_words uw ON w.id = uw.word_id AND uw.user_id = %s
            WHERE w.level IN ('A1', 'A2') AND uw.word_id IS NULL
            ORDER BY RANDOM()
            LIMIT 10
        """, (user_id,)),
        
        ("Слова для повторения", """
            SELECT w.id, w.level, w.topic, w.de, w.ru,
                   uw.interval, uw.ease_factor, uw.reps, uw.next_review
            FROM words w
            JOIN user_words uw ON w.id = uw.word_id
            WHERE w.level IN ('A1', 'A2') 
              AND uw.user_id = %s 
              AND uw.next_review <= CURRENT_TIMESTAMP 
              AND uw.status = 'learning'
            ORDER BY uw.next_review ASC
            LIMIT 10
        """, (user_id,)),
    ]
    
    results['trainer'] = []
    for desc, query, params in queries_trainer:
        # Запускаем 3 раза, берём среднее
        times = [measure_query(cur, query, params, desc) for _ in range(3)]
        avg_time = sum(times) / len(times)
        results['trainer'].append((desc, avg_time))
    
    # ============================================================
    # Тест 2: Words API - поиск
    # ============================================================
    print("\n" + "=" * 60)
    print("2️⃣  Words API - поиск с ILIKE + pg_trgm")
    print("=" * 60)
    
    queries_search = [
        ("Поиск по немецкому (ILIKE)", """
            SELECT id, de, ru, level
            FROM words
            WHERE de ILIKE %s
            ORDER BY de
            LIMIT 20
        """, ['%sch%']),
        
        ("Поиск по русскому (ILIKE)", """
            SELECT id, de, ru, level
            FROM words
            WHERE ru ILIKE %s
            ORDER BY ru
            LIMIT 20
        """, ['%дом%']),
        
        ("Поиск с pg_trgm (немецкий)", """
            SELECT id, de, ru, level
            FROM words
            WHERE de ILIKE %s
            ORDER BY similarity(de, %s) DESC
            LIMIT 20
        """, ['%mach%', 'mach']),
    ]
    
    results['search'] = []
    for desc, query, params in queries_search:
        times = [measure_query(cur, query, params, desc) for _ in range(3)]
        avg_time = sum(times) / len(times)
        results['search'].append((desc, avg_time))
    
    # ============================================================
    # Тест 3: Words API - пагинация
    # ============================================================
    print("\n" + "=" * 60)
    print("3️⃣  Words API - пагинация")
    print("=" * 60)
    
    queries_pagination = [
        ("Первая страница (A1)", """
            SELECT id, level, topic, de, ru, article
            FROM words
            WHERE level = %s
            ORDER BY id
            LIMIT %s OFFSET %s
        """, ('A1', 20, 0)),
        
        ("Вторая страница (A1)", """
            SELECT id, level, topic, de, ru, article
            FROM words
            WHERE level = %s
            ORDER BY id
            LIMIT %s OFFSET %s
        """, ('A1', 20, 20)),
        
        ("Десятая страница (A1)", """
            SELECT id, level, topic, de, ru, article
            FROM words
            WHERE level = %s
            ORDER BY id
            LIMIT %s OFFSET %s
        """, ('A1', 20, 180)),
    ]
    
    results['pagination'] = []
    for desc, query, params in queries_pagination:
        times = [measure_query(cur, query, params, desc) for _ in range(3)]
        avg_time = sum(times) / len(times)
        results['pagination'].append((desc, avg_time))
    
    # ============================================================
    # Тест 4: Stats API - агрегация
    # ============================================================
    print("\n" + "=" * 60)
    print("4️⃣  Stats API - агрегация")
    print("=" * 60)
    
    queries_stats = [
        ("Группировка по уровням", """
            SELECT level, COUNT(*)
            FROM words
            GROUP BY level
            ORDER BY level
        """, ()),
        
        ("Прогресс пользователя", """
            SELECT status, COUNT(*)
            FROM user_words
            WHERE user_id = %s
            GROUP BY status
        """, (user_id,)),
        
        ("Детально по уровням", """
            SELECT w.level, uw.status, COUNT(*)
            FROM user_words uw
            JOIN words w ON uw.word_id = w.id
            WHERE uw.user_id = %s
            GROUP BY w.level, uw.status
            ORDER BY w.level, uw.status
        """, (user_id,)),
    ]
    
    results['stats'] = []
    for desc, query, params in queries_stats:
        times = [measure_query(cur, query, params, desc) for _ in range(3)]
        avg_time = sum(times) / len(times)
        results['stats'].append((desc, avg_time))
    
    # ============================================================
    # Тест 5: Diary API
    # ============================================================
    print("\n" + "=" * 60)
    print("5️⃣  Diary API - история записей")
    print("=" * 60)
    
    # Проверяем существование таблицы
    cur.execute("SELECT to_regclass('public.diary_entries')")
    if cur.fetchone()[0]:
        queries_diary = [
            ("История записей пользователя", """
                SELECT id, original_text, corrected_text, explanation, created_at
                FROM diary_entries
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 20
            """, (user_id,)),
        ]
        
        results['diary'] = []
        for desc, query, params in queries_diary:
            times = [measure_query(cur, query, params, desc) for _ in range(3)]
            avg_time = sum(times) / len(times)
            results['diary'].append((desc, avg_time))
    else:
        print("  ⚠️  Таблица diary_entries не найдена")
        results['diary'] = []
    
    # ============================================================
    # Тест 6: Audio API
    # ============================================================
    print("\n" + "=" * 60)
    print("6️⃣  Audio API - записи")
    print("=" * 60)
    
    cur.execute("SELECT to_regclass('public.recordings')")
    if cur.fetchone()[0]:
        queries_audio = [
            ("Список записей пользователя", """
                SELECT filename, url, created_at
                FROM recordings
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 20
            """, (user_id,)),
            
            ("Старые записи (cleanup)", """
                SELECT filename
                FROM recordings
                WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '30 days'
            """, ()),
        ]
        
        results['audio'] = []
        for desc, query, params in queries_audio:
            times = [measure_query(cur, query, params, desc) for _ in range(3)]
            avg_time = sum(times) / len(times)
            results['audio'].append((desc, avg_time))
    else:
        print("  ⚠️  Таблица recordings не найдена")
        results['audio'] = []
    
    # ============================================================
    # Итоги
    # ============================================================
    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ")
    print("=" * 60)
    
    all_results = []
    for category, tests in results.items():
        all_results.extend(tests)
    
    # Сортируем по времени (худшие сначала)
    all_results.sort(key=lambda x: x[1], reverse=True)
    
    print("\n🐌 Самые медленные запросы:")
    for i, (desc, time_ms) in enumerate(all_results[:5], 1):
        status = "✅" if time_ms < 50 else ("🟡" if time_ms < 100 else "⚠️")
        print(f"  {i}. {desc}: {time_ms:.2f} мс {status}")
    
    # Проверка по целевым значениям
    print("\n🎯 Проверка по целевым значениям:")
    
    targets = {
        'trainer': 200,  # мс
        'search': 100,
        'pagination': 50,
        'stats': 50,
        'diary': 50,
        'audio': 50,
    }
    
    all_pass = True
    for category, tests in results.items():
        if not tests:
            continue
        
        target = targets.get(category, 100)
        avg = sum(t[1] for t in tests) / len(tests) if tests else 0
        status = "✅ PASS" if avg < target else "⚠️ FAIL"
        
        if avg >= target:
            all_pass = False
        
        print(f"  {category.upper()}: среднее {avg:.2f} мс (цель: <{target} мс) {status}")
    
    print("\n" + "=" * 60)
    if all_pass:
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
    else:
        print("⚠️  НЕКОТОРЫЕ ЗАПРОСЫ МЕДЛЕННЫЕ")
        print("\n💡 Рекомендации:")
        print("   - Проверьте использование индексов: EXPLAIN ANALYZE <запрос>")
        print("   - Убедитесь, что ANALYZE выполнен недавно")
        print("   - Рассмотрите кэширование для частых запросов")
    print("=" * 60)
    
    cur.close()
    conn.close()
    
    return 0 if all_pass else 1

if __name__ == "__main__":
    sys.exit(main())
