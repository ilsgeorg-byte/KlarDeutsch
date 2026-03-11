#!/usr/bin/env python3
"""
Тест API тренажёра
Проверяет, что API /trainer/words возвращает слова
"""

import os
import sys
import io
import jwt
from dotenv import load_dotenv

# Фикс для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))

# Создаём тестовый токен
SECRET_KEY = os.environ.get("JWT_SECRET", "klardeutsch-super-secret-key-change-in-production!")

def test_trainer_api():
    from db import get_db_connection
    
    # Получаем первого пользователя
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username FROM users ORDER BY id LIMIT 1")
    user = cur.fetchone()
    
    if not user:
        print("❌ Нет пользователей в БД")
        return
    
    user_id, username = user
    print(f"✅ Тестируем для пользователя: {username} (ID: {user_id})")
    
    # Создаём токен
    token = jwt.encode({
        'user_id': user_id,
        'username': username,
        'exp': 9999999999  # Далёкое будущее
    }, SECRET_KEY, algorithm="HS256")
    
    print(f"✅ Токен создан: {token[:50]}...")
    
    # Проверяем слова в БД
    print("\n📊 Статистика:")
    cur.execute("SELECT COUNT(*) FROM words WHERE level = %s", ('A1',))
    print(f"   Слов A1 в базе: {cur.fetchone()[0]}")
    
    cur.execute("SELECT COUNT(*) FROM user_words WHERE user_id = %s AND status = %s", (user_id, 'learning'))
    print(f"   Слов в изучении (у этого пользователя): {cur.fetchone()[0]}")
    
    cur.execute("""
        SELECT COUNT(*) FROM user_words uw 
        JOIN words w ON uw.word_id = w.id
        WHERE uw.user_id = %s AND uw.status = %s AND uw.next_review <= CURRENT_TIMESTAMP
    """, (user_id, 'learning'))
    result = cur.fetchone()[0]
    print(f"   Слов на повторение СЕЙЧАС: {result}")
    
    # Проверяем запрос, который использует API
    print("\n🔍 Проверка SQL запроса API:")
    cur.execute("""
        SELECT w.id, w.level, w.de, w.ru, uw.next_review
        FROM words w
        JOIN user_words uw ON w.id = uw.word_id
        WHERE w.level IN %s AND uw.user_id = %s 
          AND uw.next_review <= CURRENT_TIMESTAMP 
          AND uw.status = 'learning'
        ORDER BY uw.next_review ASC
        LIMIT 10
    """, (('A1', 'A2', 'B1', 'B2', 'C1'), user_id))
    
    rows = cur.fetchall()
    print(f"   Найдено слов для повторения: {len(rows)}")
    if rows:
        print("   Первые 5 слов:")
        for row in rows[:5]:
            print(f"      - {row[2]} ({row[3]})")
    
    # Проверяем новые слова
    print("\n🔍 Проверка новых слов:")
    cur.execute("""
        SELECT w.id, w.level, w.de, w.ru
        FROM words w
        LEFT JOIN user_words uw ON w.id = uw.word_id AND uw.user_id = %s
        WHERE w.level IN %s AND uw.word_id IS NULL
        ORDER BY RANDOM()
        LIMIT 10
    """, (user_id, ('A1', 'A2', 'B1', 'B2', 'C1')))
    
    rows = cur.fetchall()
    print(f"   Найдено новых слов: {len(rows)}")
    if rows:
        print("   Первые 5 слов:")
        for row in rows[:5]:
            print(f"      - {row[2]} ({row[3]})")
    
    cur.close()
    conn.close()
    
    print("\n✅ Тест завершён!")
    print(f"\n💡 Токен для тестов в браузере:")
    print(f"   localStorage.setItem('token', '{token}')")

if __name__ == "__main__":
    test_trainer_api()
