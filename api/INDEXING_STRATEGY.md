# Strategic Database Indexing Strategy

## Overview
This document outlines the strategic indexing approach implemented to optimize database performance for the KlarDeutsch application. The indexing strategy focuses on the most frequently accessed query patterns and performance bottlenecks.

## Tables and Indexes

### Words Table (`words`)
The `words` table contains vocabulary entries and is the most frequently queried table.

#### Applied Indexes:
1. **`idx_words_level`** - Single column index on `level`
   - Purpose: Optimizes level-based queries (e.g., `/api/words?level=A1`)
   - Query Pattern: `WHERE level = ?`

2. **`idx_words_topic`** - Single column index on `topic`
   - Purpose: Optimizes topic-based queries (e.g., `/api/words/by-topic/{topic}`)
   - Query Pattern: `WHERE topic = ?`

3. **`idx_words_level_user_id`** - Composite index on `(level, user_id)`
   - Purpose: Optimizes personalized level-based queries
   - Query Pattern: `WHERE level = ? AND (user_id IS NULL OR user_id = ?)`

4. **`idx_words_user_id`** - Single column index on `user_id`
   - Purpose: Optimizes personal word queries
   - Query Pattern: `WHERE user_id = ?`

5. **`idx_words_de_gin`** - GIN index using `to_tsvector('german', de)`
   - Purpose: Optimizes full-text search on German words
   - Query Pattern: Text search functionality

6. **`idx_words_ru_gin`** - GIN index using `to_tsvector('russian', ru)`
   - Purpose: Optimizes full-text search on Russian words
   - Query Pattern: Text search functionality

7. **`idx_words_de_text_pattern_ops`** - Pattern matching index on `de`
   - Purpose: Optimizes LIKE/ILIKE operations for German text search
   - Query Pattern: `WHERE de ILIKE ?`

8. **`idx_words_ru_text_pattern_ops`** - Pattern matching index on `ru`
   - Purpose: Optimizes LIKE/ILIKE operations for Russian text search
   - Query Pattern: `WHERE ru ILIKE ?`

9. **`idx_words_id`** - Single column index on `id`
   - Purpose: Optimizes ID-based ordering and pagination
   - Query Pattern: `ORDER BY id`

### User Words Table (`user_words`)
The `user_words` table tracks individual user progress using the SM-2 algorithm.

#### Applied Indexes:
1. **`idx_user_words_next_review`** - Single column index on `next_review`
   - Purpose: Critical for trainer functionality - finding words to review
   - Query Pattern: `WHERE next_review <= CURRENT_TIMESTAMP`

2. **`idx_user_words_user_review`** - Composite index on `(user_id, next_review)`
   - Purpose: Optimizes user-specific review queries
   - Query Pattern: `WHERE user_id = ? AND next_review <= CURRENT_TIMESTAMP`

3. **`idx_user_words_user_status`** - Composite index on `(user_id, status)`
   - Purpose: Optimizes user progress statistics and filtering by status
   - Query Pattern: `WHERE user_id = ? AND status = ?`

4. **`idx_user_words_user_id`** - Single column index on `user_id`
   - Purpose: General user-specific queries
   - Query Pattern: `WHERE user_id = ?`

5. **`idx_user_words_word_id`** - Single column index on `word_id`
   - Purpose: Optimizes joins with the words table
   - Query Pattern: JOIN operations

### User Favorites Table (`user_favorites`)
The `user_favorites` table manages user's favorite words.

#### Applied Indexes:
1. **`idx_user_favorites_user_id`** - Single column index on `user_id`
   - Purpose: Optimizes fetching user's favorites
   - Query Pattern: `WHERE user_id = ?`

2. **`idx_user_favorites_word_id`** - Single column index on `word_id`
   - Purpose: Optimizes joins and checks for favorite status
   - Query Pattern: JOIN operations and existence checks

3. **`idx_user_favorites_user_word`** - Composite index on `(user_id, word_id)`
   - Purpose: Optimizes favorite toggle operations
   - Query Pattern: `WHERE user_id = ? AND word_id = ?`

### User Word Notes Table (`user_word_notes`)
The `user_word_notes` table stores user notes for specific words.

#### Applied Indexes:
1. **`idx_user_word_notes_user_word`** - Composite index on `(user_id, word_id)`
   - Purpose: Optimizes note retrieval for specific user-word combinations
   - Query Pattern: `WHERE user_id = ? AND word_id = ?`

### Recordings Table (`recordings`)
The `recordings` table stores user audio recordings.

#### Applied Indexes:
1. **`idx_recordings_user_id`** - Single column index on `user_id`
   - Purpose: Optimizes user-specific recording queries
   - Query Pattern: `WHERE user_id = ?`

## Performance Impact

### Critical Query Optimizations:
1. **Level-based word retrieval** - Improved by `idx_words_level` and `idx_words_level_user_id`
2. **Trainer functionality** - Significantly improved by `idx_user_words_next_review` and `idx_user_words_user_review`
3. **Text search** - Enhanced by GIN indexes and pattern matching indexes
4. **Favorite operations** - Optimized by composite indexes on user-word pairs
5. **Topic-based queries** - Improved by `idx_words_topic`

### Expected Improvements:
- Level-based queries: 5-10x faster
- Trainer word retrieval: 10-50x faster (especially for users with many words)
- Text search: 3-5x faster
- Favorite operations: 5-10x faster
- Topic-based queries: 5-10x faster

## Maintenance Considerations

### Index Size:
- Monitor index sizes regularly as the database grows
- Consider partial indexes for very large datasets if needed

### Update Performance:
- Indexes will slightly slow down INSERT/UPDATE operations
- Trade-off is acceptable given the significant read performance gains

### Monitoring:
- Regularly monitor query plans to ensure indexes are being used
- Use `EXPLAIN ANALYZE` for slow queries to verify index usage

## Future Enhancements

### Potential Additional Indexes:
1. **Partial indexes** for specific use cases if data volume increases significantly
2. **Expression indexes** for complex query patterns that emerge
3. **Cover indexes** if specific queries consistently select the same columns

### Monitoring Queries:
```sql
-- Check index usage
SELECT schemaname, tablename, indexname, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes;

-- Find unused indexes
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0;
```

## Conclusion

This strategic indexing approach addresses the primary performance bottlenecks in the KlarDeutsch application. The indexes are specifically tailored to the most common query patterns found in the API routes, ensuring optimal performance for user experience while maintaining reasonable write performance.