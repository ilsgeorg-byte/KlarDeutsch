-- Дополнительные критические индексы для производительности KlarDeutsch

-- 1. Ускорение выборки слов для ПОВТОРЕНИЯ (основной запрос тренажера)
-- Позволяет мгновенно найти слова со статусом 'learning' и просроченной датой next_review
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_words_review_queue 
ON user_words (user_id, status, next_review ASC) 
WHERE status = 'learning';

-- 2. Ускорение поиска НОВЫХ слов (учет уровня и исключение уже существующих в user_words)
-- Помогает LEFT JOIN работать быстрее
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_words_level_id 
ON words (level, id);

-- 3. Ускорение детальной статистики (JOIN user_words и words)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_words_user_status_word
ON user_words (user_id, status, word_id);

-- 4. Обновление статистики для планировщика
ANALYZE user_words;
ANALYZE words;
