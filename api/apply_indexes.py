#!/usr/bin/env python3
"""
Скрипт оптимизации базы данных KlarDeutsch
Применяет индексы для ускорения SQL-запросов
"""

import os
import sys
import io
from dotenv import load_dotenv

# Фикс для Windows: устанавливаем UTF-8 для stdout
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Загружаем переменные окружения
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))

import psycopg2
from psycopg2.extras import RealDictCursor

def get_connection():
    url = os.environ.get("POSTGRES_URL")
    if not url:
        raise Exception("POSTGRES_URL не найдена в .env.local")
    return psycopg2.connect(url)

def check_extension_exists(cur, extension_name):
    """Проверяет, установлено ли расширение"""
    cur.execute("SELECT 1 FROM pg_extension WHERE extname = %s", (extension_name,))
    return cur.fetchone() is not None

def check_index_exists(cur, index_name):
    """Проверяет, существует ли индекс"""
    cur.execute("""
        SELECT 1 FROM pg_indexes 
        WHERE indexname = %s AND schemaname = 'public'
    """, (index_name,))
    return cur.fetchone() is not None

def create_index_safe(cur, conn, index_name, create_sql):
    """Создаёт индекс, если он не существует"""
    if check_index_exists(cur, index_name):
        print(f"  ⚡ {index_name} — уже существует")
        return False
    
    try:
        print(f"  📝 {index_name} — создаём...")
        # CONCURRENTLY не работает в транзакции, поэтому делаем commit перед и после
        conn.commit()
        cur.execute(create_sql.replace("CONCURRENTLY", ""))  # Убираем CONCURRENTLY для работы в транзакции
        print(f"  ✅ {index_name} — создан")
        return True
    except Exception as e:
        print(f"  ❌ {index_name} — ошибка: {e}")
        conn.rollback()
        return False

def main():
    print("=" * 60)
    print("🔧 Оптимизация базы данных KlarDeutsch")
    print("=" * 60)
    
    conn = None
    created_count = 0
    error_count = 0
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        print("\n📊 Подключение к базе данных... ✅")
        
        # Получение размера таблиц
        cur.execute("""
            SELECT relname, n_live_tup 
            FROM pg_stat_user_tables 
            WHERE schemaname = 'public'
            ORDER BY n_live_tup DESC
        """)
        print("\n📈 Размер таблиц:")
        for row in cur.fetchall():
            print(f"   {row[0]}: {row[1]:,} строк")
        
        # ============================================================
        # 1. Trainer API индексы
        # ============================================================
        print("\n" + "=" * 60)
        print("1️⃣  Trainer API — индексы для выборки слов")
        print("=" * 60)
        
        indexes = [
            ("idx_user_words_user_level", 
             "CREATE INDEX CONCURRENTLY idx_user_words_user_level ON user_words (user_id, word_id)"),
            
            ("idx_words_level", 
             "CREATE INDEX CONCURRENTLY idx_words_level ON words (level)"),
            
            ("idx_user_words_word_user", 
             "CREATE INDEX CONCURRENTLY idx_user_words_word_user ON user_words (word_id, user_id)"),
        ]
        
        for name, sql in indexes:
            if create_index_safe(cur, conn, name, sql):
                created_count += 1
        
        # ============================================================
        # 2. pg_trgm расширение для поиска
        # ============================================================
        print("\n" + "=" * 60)
        print("2️⃣  Поиск — расширение pg_trgm")
        print("=" * 60)
        
        if not check_extension_exists(cur, 'pg_trgm'):
            print("  📝 Установка расширения pg_trgm...")
            try:
                cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
                print("  ✅ pg_trgm — установлено")
                created_count += 1
            except Exception as e:
                print(f"  ⚠️  pg_trgm — ошибка: {e}")
                print("  💡 Возможно, требуется суперпользователь для установки расширения")
                error_count += 1
        else:
            print("  ✅ pg_trgm — уже установлено")
        
        # Индексы для поиска
        search_indexes = [
            ("idx_words_de_trgm", 
             "CREATE INDEX CONCURRENTLY idx_words_de_trgm ON words USING GIN (de gin_trgm_ops)"),
            
            ("idx_words_ru_trgm", 
             "CREATE INDEX CONCURRENTLY idx_words_ru_trgm ON words USING GIN (ru gin_trgm_ops)"),
        ]
        
        for name, sql in search_indexes:
            if create_index_safe(cur, conn, name, sql):
                created_count += 1
        
        # ============================================================
        # 3. Audio API индексы
        # ============================================================
        print("\n" + "=" * 60)
        print("3️⃣  Audio API — индексы для записей")
        print("=" * 60)
        
        # Проверяем существование таблицы recordings
        cur.execute("SELECT to_regclass('public.recordings')")
        if cur.fetchone()[0]:
            audio_indexes = [
                ("idx_recordings_created_at", 
                 "CREATE INDEX CONCURRENTLY idx_recordings_created_at ON recordings (created_at)"),
                
                ("idx_recordings_user_created", 
                 "CREATE INDEX CONCURRENTLY idx_recordings_user_created ON recordings (user_id, created_at DESC)"),
            ]
            
            for name, sql in audio_indexes:
                if create_index_safe(cur, conn, name, sql):
                    created_count += 1
        else:
            print("  ⚠️  Таблица recordings не найдена — пропускаем")
        
        # ============================================================
        # 4. Diary API индексы
        # ============================================================
        print("\n" + "=" * 60)
        print("4️⃣  Diary API — индексы для записей дневника")
        print("=" * 60)
        
        # Проверяем существование таблицы diary_entries
        cur.execute("SELECT to_regclass('public.diary_entries')")
        if cur.fetchone()[0]:
            diary_indexes = [
                ("idx_diary_user_created", 
                 "CREATE INDEX CONCURRENTLY idx_diary_user_created ON diary_entries (user_id, created_at DESC)"),
            ]
            
            for name, sql in diary_indexes:
                if create_index_safe(cur, conn, name, sql):
                    created_count += 1
        else:
            print("  ⚠️  Таблица diary_entries не найдена — пропускаем")
        
        # ============================================================
        # 5. Stats API индексы
        # ============================================================
        print("\n" + "=" * 60)
        print("5️⃣  Stats API — индексы для агрегации")
        print("=" * 60)
        
        stats_indexes = [
            ("idx_words_level_topic", 
             "CREATE INDEX CONCURRENTLY idx_words_level_topic ON words (level, topic)"),
            
            ("idx_user_words_status", 
             "CREATE INDEX CONCURRENTLY idx_user_words_status ON user_words (user_id, status)"),
        ]
        
        for name, sql in stats_indexes:
            if create_index_safe(cur, conn, name, sql):
                created_count += 1
        
        # ============================================================
        # 6. Favorites API индексы
        # ============================================================
        print("\n" + "=" * 60)
        print("6️⃣  Favorites API — индексы для избранного")
        print("=" * 60)
        
        fav_indexes = [
            ("idx_user_favorites_word", 
             "CREATE INDEX CONCURRENTLY idx_user_favorites_word ON user_favorites (word_id, user_id)"),
        ]
        
        for name, sql in fav_indexes:
            if create_index_safe(cur, conn, name, sql):
                created_count += 1
        
        # ============================================================
        # 7. Обновление статистики (ANALYZE)
        # ============================================================
        print("\n" + "=" * 60)
        print("7️⃣  Обновление статистики (ANALYZE)")
        print("=" * 60)
        
        tables = ['words', 'user_words', 'user_favorites']
        
        # Проверяем существование таблиц перед ANALYZE
        for table in tables:
            cur.execute(f"SELECT to_regclass('public.{table}')")
            if cur.fetchone()[0]:
                print(f"  📊 ANALYZE {table}...")
                cur.execute(f"ANALYZE {table}")
                print(f"  ✅ {table} — обновлено")
        
        # Проверяем diary_entries и recordings
        for table in ['diary_entries', 'recordings']:
            cur.execute(f"SELECT to_regclass('public.{table}')")
            if cur.fetchone()[0]:
                print(f"  📊 ANALYZE {table}...")
                cur.execute(f"ANALYZE {table}")
                print(f"  ✅ {table} — обновлено")
        
        # Сохраняем изменения
        conn.commit()
        
        # ============================================================
        # Итоги
        # ============================================================
        print("\n" + "=" * 60)
        print("✅ ОПТИМИЗАЦИЯ ЗАВЕРШЕНА")
        print("=" * 60)
        print(f"\n📊 Результаты:")
        print(f"   Создано индексов: {created_count}")
        print(f"   Ошибок: {error_count}")
        
        # Показываем список всех индексов
        print("\n📋 Созданные индексы:")
        cur.execute("""
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE schemaname = 'public' AND indexname LIKE 'idx_%'
            ORDER BY indexname
        """)
        
        for row in cur.fetchall():
            print(f"   • {row[0]}")
        
        cur.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("💡 Следующие шаги:")
        print("   1. Проверьте время поиска слов (цель: <100ms)")
        print("   2. Настройте еженедельный ANALYZE")
        print("   3. При >5,000 слов: проверьте работу pg_trgm")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        print(f"Тип ошибки: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    sys.exit(main())
