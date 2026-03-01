-- ================================================================
-- OPTIMIZATION SCRIPT для KlarDeutsch
-- Индексы для ускорения SQL-запросов
-- ================================================================
-- Запуск: psql $POSTGRES_URL -f optimize_indexes.sql
-- ================================================================

-- ----------------------------------------------------------------
-- 1. Trainer API: Ускорение выборки слов для тренировки
-- ----------------------------------------------------------------
-- Проблема: ORDER BY RANDOM() с LEFT JOIN медленно на больших данных
-- Решение: Индекс покрывает WHERE и JOIN условия

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_words_user_level
ON user_words (user_id, word_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_words_level
ON words (level);

-- Композитный индекс для новых слов (LEFT JOIN фильтр)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_words_word_user
ON user_words (word_id, user_id);

-- ----------------------------------------------------------------
-- 2. Words API: Поиск по тексту (ILIKE запросы)
-- ----------------------------------------------------------------
-- Проблема: ILIKE с wildcard в начале (%query%) не использует индексы
-- Решение: pg_trgm расширение для нечеткого поиска

-- Включить расширение (требуется один раз)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- GIN индекс для быстрого поиска по немецким словам
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_words_de_trgm
ON words USING GIN (de gin_trgm_ops);

-- GIN индекс для поиска по русским словам
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_words_ru_trgm
ON words USING GIN (ru gin_trgm_ops);

-- ----------------------------------------------------------------
-- 3. Audio API: Выборка старых записей для очистки
-- ----------------------------------------------------------------
-- Проблема: WHERE created_at < %s без индекса делает full scan
-- Решение: Индекс по created_at

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_recordings_created_at
ON recordings (created_at);

-- Композитный индекс для list_audio (user_id + created_at)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_recordings_user_created
ON recordings (user_id, created_at DESC);

-- ----------------------------------------------------------------
-- 4. Diary API: История записей
-- ----------------------------------------------------------------
-- Проблема: ORDER BY created_at DESC для конкретного пользователя
-- Решение: Композитный индекс

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_diary_user_created
ON diary_entries (user_id, created_at DESC);

-- ----------------------------------------------------------------
-- 5. Stats API: Агрегация по уровням и статусам
-- ----------------------------------------------------------------
-- Проблема: GROUP BY level и status на больших таблицах
-- Решение: Индексы для группировки

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_words_level_topic
ON words (level, topic);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_words_status
ON user_words (user_id, status);

-- ----------------------------------------------------------------
-- 6. Favorites API: Быстрая проверка избранных
-- ----------------------------------------------------------------
-- Уже есть PRIMARY KEY (user_id, word_id), но добавим для JOIN

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_favorites_word
ON user_favorites (word_id, user_id);

-- ----------------------------------------------------------------
-- 7. Общие рекомендации
-- ----------------------------------------------------------------

-- ANALYZE обновляет статистику для планировщика запросов
ANALYZE words;
ANALYZE user_words;
ANALYZE recordings;
ANALYZE diary_entries;
ANALYZE user_favorites;

-- ----------------------------------------------------------------
-- Проверка созданных индексов
-- ----------------------------------------------------------------
-- SELECT indexname, indexdef 
-- FROM pg_indexes 
-- WHERE schemaname = 'public' 
-- ORDER BY tablename, indexname;

-- ----------------------------------------------------------------
-- Мониторинг производительности (после применения)
-- ----------------------------------------------------------------
-- SELECT relname, idx_scan, idx_tup_read, idx_tup_fetch
-- FROM pg_stat_user_indexes
-- ORDER BY idx_scan DESC;

-- ----------------------------------------------------------------
-- Удаление неиспользуемых индексов (опционально)
-- ----------------------------------------------------------------
-- SELECT indexrelname, idx_scan
-- FROM pg_stat_user_indexes
-- WHERE idx_scan = 0;
-- -- DROP INDEX CONCURRENTLY IF EXISTS unused_index;
