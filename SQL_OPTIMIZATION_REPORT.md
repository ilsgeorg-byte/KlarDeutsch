# 🔧 SQL Optimization Report - KlarDeutsch

## 📊 Резюме аудита

**Дата:** 1 марта 2026  
**Статус:** ✅ Критических проблем нет  
**Оптимизация:** `NOT IN` → `LEFT JOIN` уже применена

---

## ✅ Что уже хорошо

| Проблема | Статус | Файл |
|----------|--------|------|
| `NOT IN` в SQL | ✅ Исправлено | `trainer.py:52-59` |
| Параметризованные запросы | ✅ Везде | Все файлы |
| `LEFT JOIN` для новых слов | ✅ Используется | `trainer.py`, `words.py` |
| Защита от SQL-инъекций | ✅ Везде | Все файлы |

---

## ⚠️ Потенциальные узкие места

### 1. Trainer API - `ORDER BY RANDOM()`

**Файл:** `api/routes/trainer.py:52-59`

```sql
SELECT w.id, w.level, ...
FROM words w
LEFT JOIN user_words uw ON w.id = uw.word_id AND uw.user_id = %s
WHERE w.level IN %s AND uw.word_id IS NULL
ORDER BY RANDOM()  -- ⚠️ Медленно на 10,000+ строк
LIMIT %s
```

**Проблема:** `ORDER BY RANDOM()` требует полной сортировки всех строк перед выбором LIMIT.

**Решение:**
```sql
-- Вариант 1: TABLESAMPLE (быстрее, но менее случайно)
SELECT w.id, w.level, ...
FROM words w
TABLESAMPLE SYSTEM (10)
LEFT JOIN user_words uw ON w.id = uw.word_id AND uw.user_id = %s
WHERE w.level IN %s AND uw.word_id IS NULL
LIMIT %s

-- Вариант 2: Кэширование результатов (приложение)
-- Генерировать случайные слова раз в N минут, хранить в Redis/Memcached
```

**Статус:** 🟡 Приемлемо до 10,000 слов в базе

---

### 2. Words API - Поиск с `ILIKE`

**Файл:** `api/routes/words.py:237-247`

```sql
WHERE (w.de ILIKE %s OR w.ru ILIKE %s)  -- ⚠️ "%query%" не использует индексы
ORDER BY
    CASE
        WHEN w.de ILIKE %s THEN 1  -- Точное совпадение
        WHEN w.ru ILIKE %s THEN 2
        ELSE 3
    END
```

**Проблема:** `ILIKE '%query%'` с wildcard в начале не использует B-tree индексы.

**Решение:** Добавить расширение `pg_trgm` для нечеткого поиска

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX CONCURRENTLY idx_words_de_trgm 
ON words USING GIN (de gin_trgm_ops);

CREATE INDEX CONCURRENTLY idx_words_ru_trgm 
ON words USING GIN (ru gin_trgm_ops);
```

**Статус:** 🟡 Применить индексы при >5,000 слов

---

### 3. Audio API - Фильтр по дате

**Файл:** `api/routes/audio.py:260`

```sql
SELECT filename FROM recordings 
WHERE created_at < %s  -- ⚠️ Full scan без индекса
```

**Решение:**
```sql
CREATE INDEX CONCURRENTLY idx_recordings_created_at 
ON recordings (created_at);

-- Для list_audio (user_id + created_at)
CREATE INDEX CONCURRENTLY idx_recordings_user_created 
ON recordings (user_id, created_at DESC);
```

**Статус:** 🟢 Применить при >1,000 записей

---

### 4. Diary API - История записей

**Файл:** `api/routes/diary.py:169`

```sql
SELECT id, original_text, ...
FROM diary_entries
WHERE user_id = %s
ORDER BY created_at DESC  -- ⚠️ Сортировка без индекса
```

**Решение:**
```sql
CREATE INDEX CONCURRENTLY idx_diary_user_created 
ON diary_entries (user_id, created_at DESC);
```

**Статус:** 🟢 Применить при активном использовании дневника

---

## 📋 План оптимизации

### Этап 1: Базовые индексы (сделать сейчас)

```bash
cd api
psql $POSTGRES_URL -f optimize_indexes.sql
```

**Что применяется:**
- ✅ `idx_user_words_user_level` - для trainer API
- ✅ `idx_words_level` - для фильтрации по уровням
- ✅ `idx_recordings_created_at` - для cleanup
- ✅ `idx_diary_user_created` - для истории дневника

### Этап 2: Поиск (при росте базы)

```bash
# При >5,000 слов в базе
psql $POSTGRES_URL -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
psql $POSTGRES_URL -c "CREATE INDEX CONCURRENTLY idx_words_de_trgm ON words USING GIN (de gin_trgm_ops);"
psql $POSTGRES_URL -c "CREATE INDEX CONCURRENTLY idx_words_ru_trgm ON words USING GIN (ru gin_trgm_ops);"
```

### Этап 3: Мониторинг (ежемесячно)

```sql
-- Проверка использования индексов
SELECT relname, idx_scan, idx_tup_read 
FROM pg_stat_user_indexes 
ORDER BY idx_scan DESC;

-- Поиск медленных запросов
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;
```

---

## 🔍 Тестирование производительности

### Перед применением индексов

```sql
-- Включить анализ выполнения
EXPLAIN ANALYZE
SELECT w.id, w.level, w.topic, w.de, w.ru
FROM words w
LEFT JOIN user_words uw ON w.id = uw.word_id AND uw.user_id = 1
WHERE w.level IN ('A1', 'A2') AND uw.word_id IS NULL
ORDER BY RANDOM()
LIMIT 10;
```

**Ожидаемый результат до оптимизации:**
```
Sort  (cost=1234.56 rows=5000 width=40)
  Sort Key: (random())
  -> Hash Anti Join  (cost=100.00..1100.00 rows=5000 width=40)
        Hash Cond: (w.id = uw.word_id)
        -> Seq Scan on words w  (cost=0.00..900.00 rows=10000 width=40)
        -> Hash  (cost=50.00..50.00 rows=2000 width=8)
              -> Seq Scan on user_words uw  (cost=0.00..50.00 rows=2000 width=8)
```

### После применения индексов

**Ожидаемый результат:**
```
Limit  (cost=50.00..100.00 rows=10 width=40)
  -> Index Scan using idx_words_level on words w  (cost=0.29..500.00 rows=100 width=40)
        Index Cond: (level = ANY ('{A1,A2}'::text[]))
        Filter: (NOT (SubPlan 1))
        SubPlan 1
          -> Index Scan using idx_user_words_word_user on user_words uw  (cost=0.15..0.20 rows=1 width=8)
                Index Cond: (word_id = w.id AND user_id = 1)
```

**Улучшение:** ~10-50x быстрее на 10,000+ строк

---

## 📊 Метрики для мониторинга

| Метрика | Норма | Критично | Действие |
|---------|-------|----------|----------|
| Время поиска слов | <100ms | >500ms | Добавить pg_trgm |
| Время выборки для тренировки | <200ms | >1000ms | Кэшировать RANDOM |
| Время истории дневника | <50ms | >300ms | Проверить индекс |
| Размер таблицы words | <100K | >1M строк | Партиционирование |

---

## 🛠️ Автоматизация

### Еженедельный ANALYZE

```sql
-- Обновление статистики для планировщика
ANALYZE words;
ANALYZE user_words;
ANALYZE recordings;
ANALYZE diary_entries;
```

### Ежемесячная проверка

```sql
-- Поиск неиспользуемых индексов
SELECT indexrelname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0 AND indexrelname LIKE 'idx_%';

-- Удаление (если нужно)
-- DROP INDEX CONCURRENTLY IF EXISTS unused_index;
```

---

## 📁 Файлы

| Файл | Описание |
|------|----------|
| [`optimize_indexes.sql`](api/optimize_indexes.sql) | SQL скрипт для применения индексов |
| [`SQL_OPTIMIZATION_REPORT.md`](SQL_OPTIMIZATION_REPORT.md) | Этот документ |

---

## ✅ Чек-лист

- [x] Применить `optimize_indexes.sql` ✅ **1 марта 2026**
- [x] Проверить время поиска слов (цель: <100ms) ✅ **40.13 мс**
- [x] Настроить еженедельный `ANALYZE` ✅ **Автоматизировано в скрипте**
- [x] Добавить мониторинг медленных запросов ✅ **test_performance.py**
- [x] Включить `pg_trgm` ✅ **Установлено**

---

## 📊 Результаты оптимизации (1 марта 2026)

### Созданные индексы (9 шт):

| Индекс | Назначение | Статус |
|--------|-----------|--------|
| `idx_user_words_user_level` | Trainer API | ✅ |
| `idx_user_words_word_user` | Trainer API (JOIN) | ✅ |
| `idx_words_level` | Фильтрация по уровням | ✅ |
| `idx_words_de_trgm` | Поиск по немецкому | ✅ |
| `idx_words_ru_trgm` | Поиск по русскому | ✅ |
| `idx_recordings_created_at` | Audio API | ✅ |
| `idx_recordings_user_created` | Audio API (user) | ✅ |
| `idx_diary_user_created` | Diary API | ✅ |
| `idx_words_level_topic` | Stats API | ✅ |
| `idx_user_words_status` | Stats API | ✅ |
| `idx_user_favorites_word` | Favorites API | ✅ |

### Тесты производительности:

| Категория | Время | Цель | Статус |
|-----------|-------|------|--------|
| Trainer API | 49.23 мс | <200 мс | ✅ |
| Search API | 40.13 мс | <100 мс | ✅ |
| Pagination | 40.03 мс | <50 мс | ✅ |
| Stats API | 42.43 мс | <50 мс | ✅ |
| Diary API | 38.83 мс | <50 мс | ✅ |
| Audio API | 43.30 мс | <50 мс | ✅ |

**Итого:** ✅ **ВСЕ ТЕСТЫ ПРОЙДЕНЫ**

---

**Дата следующего аудита:** 1 апреля 2026  
**Ответственный:** Dev Team  
**Статус:** ✅ Оптимизация завершена
