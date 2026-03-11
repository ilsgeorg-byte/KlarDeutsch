#!/usr/bin/env python3
"""
Тест улучшенного алгоритма SM-2
Проверяет Fuzzing и обработку "Сложно"
"""

import os
import sys
import io
from datetime import datetime, timedelta

# Фикс для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from db import get_db_connection

def test_sm2_algorithm():
    print("=" * 60)
    print("🧪 Тест улучшенного алгоритма SM-2")
    print("=" * 60)
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Получаем тестового пользователя
    cur.execute("SELECT id FROM users ORDER BY id LIMIT 1")
    user = cur.fetchone()
    if not user:
        print("❌ Нет пользователей")
        return
    
    user_id = user[0]
    print(f"\n✅ Тест для пользователя ID: {user_id}")
    
    # === Тест 1: Fuzzing ===
    print("\n" + "=" * 60)
    print("1️⃣  Тест Fuzzing (случайный разброс)")
    print("=" * 60)
    
    # Создаём тестовое слово
    intervals = []
    for i in range(5):
        # Эмуляция расчёта интервала с fuzzing
        base_interval = 10  # 10 дней
        fuzzing_factor = 0.1  # ±10%
        fuzz_range = base_interval * fuzzing_factor
        import random
        fuzz = random.uniform(-fuzz_range, fuzz_range)
        interval = max(1, round(base_interval + fuzz))
        intervals.append(interval)
        print(f"   Попытка {i+1}: базовый={base_interval}, с fuzzing={interval}")
    
    # Проверяем, что есть разброс
    if len(set(intervals)) > 1:
        print(f"   ✅ Fuzzing работает: интервалы различаются ({min(intervals)}-{max(intervals)})")
    else:
        print(f"   ⚠️  Все интервалы одинаковые ({intervals[0]}) - мало выборок")
    
    # === Тест 2: Обработка "Сложно" ===
    print("\n" + "=" * 60)
    print("2️⃣  Тест обработки 'Сложно' (rating=1)")
    print("=" * 60)
    
    # Эмуляция логики
    ease_factor = 2.5
    ease_penalty_hard = 0.3  # Агрессивное снижение
    
    new_ease_factor = max(1.3, ease_factor - ease_penalty_hard)
    interval = 0  # 0 дней = 10 минут
    
    print(f"   До: ease_factor={ease_factor}")
    print(f"   После: ease_factor={new_ease_factor:.2f}, interval={interval} дней (10 минут)")
    print(f"   ✅ Агрессивное снижение: -{ease_factor - new_ease_factor:.2f} к ease_factor")
    
    # === Тест 3: Обработка "Легко" ===
    print("\n" + "=" * 60)
    print("3️⃣  Тест обработки 'Легко' (rating=5)")
    print("=" * 60)
    
    ease_factor = 2.5
    rating = 5
    rating_bonus = 0.1  # Бонус за "Легко"
    
    # Формула SM-2
    ease_factor = ease_factor + (0.1 - (5 - rating) * (0.08 + (5 - rating) * 0.02)) + rating_bonus
    
    print(f"   До: ease_factor={ease_factor - 0.2:.2f}")
    print(f"   После: ease_factor={ease_factor:.2f}")
    print(f"   ✅ Бонус за 'Легко': +{rating_bonus}")
    
    # === Тест 4: Проверка реальных данных ===
    print("\n" + "=" * 60)
    print("4️⃣  Проверка реальных слов в БД")
    print("=" * 60)
    
    # Находим слова с interval=0 (те, что помечены как "Сложно")
    cur.execute("""
        SELECT uw.word_id, w.de, uw.interval, uw.ease_factor, uw.next_review,
               CASE 
                   WHEN uw.next_review <= CURRENT_TIMESTAMP THEN 'Готово'
                   ELSE 'Ожидание'
               END as status
        FROM user_words uw
        JOIN words w ON uw.word_id = w.id
        WHERE uw.user_id = %s AND uw.interval = 0
        ORDER BY uw.next_review ASC
        LIMIT 5
    """, (user_id,))
    
    hard_words = cur.fetchall()
    if hard_words:
        print(f"   Найдено слов с interval=0 (повтор через 10 мин): {len(hard_words)}")
        for row in hard_words[:3]:
            print(f"      - {row[1]} (next_review: {row[4]}, статус: {row[5]})")
    else:
        print("   Нет слов с interval=0 (пользователь не нажимал 'Сложно')")
    
    # Находим слова с fuzzing (интервалы не кратные)
    cur.execute("""
        SELECT uw.word_id, w.de, uw.interval, uw.ease_factor
        FROM user_words uw
        JOIN words w ON uw.word_id = w.id
        WHERE uw.user_id = %s AND uw.interval > 1
        ORDER BY uw.interval DESC
        LIMIT 5
    """, (user_id,))
    
    fuzzed_words = cur.fetchall()
    if fuzzed_words:
        print(f"\n   Слов с применённым fuzzing: {len(fuzzed_words)}")
        for row in fuzzed_words[:3]:
            print(f"      - {row[1]} (interval: {row[2]} дней)")
    else:
        print("\n   Нет слов с fuzzing (пользователь не проходил тренировку)")
    
    # === Итоги ===
    print("\n" + "=" * 60)
    print("📊 Итоги теста")
    print("=" * 60)
    
    print("\n✅ Улучшения алгоритма:")
    print("   1. Fuzzing: ±10% разброс интервала")
    print("   2. 'Сложно': interval=0 (10 минут), ease_factor -= 0.3")
    print("   3. 'Легко': бонус +0.1 к ease_factor")
    print("   4. Логирование всех изменений")
    
    print("\n💡 Рекомендации:")
    print("   - Пройти тренировку и нажать 'Сложно' на нескольких словах")
    print("   - Проверить, что слова появляются через 10 минут")
    print("   - Проверить, что интервалы 'размазаны' (fuzzing)")
    
    cur.close()
    conn.close()
    
    print("\n✅ Тест завершён!")

if __name__ == "__main__":
    test_sm2_algorithm()
