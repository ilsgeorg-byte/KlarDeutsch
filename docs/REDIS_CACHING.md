# Redis Кэширование в KlarDeutsch

## 📋 Обзор

KlarDeutsch использует Redis для кэширования ответов API, что значительно улучшает производительность:

- **⚡ Быстрые ответы:** 5-15ms вместо 50-200ms
- **📉 Меньше нагрузка на БД:** до 80% запросов обслуживаются из кэша
- **📈 Лучшая масштабируемость:** поддержка больших пиковых нагрузок

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Запуск Redis

**Вариант A: Docker (рекомендуется)**
```bash
docker-compose up -d redis
```

**Вариант B: Локальный Redis**
- Установите Redis с https://redis.io/download
- Запустите: `redis-server`

### 3. Настройка переменных окружения

Скопируйте `.env.local.example` в `.env.local`:

```bash
cp .env.local.example .env.local
```

Проверьте настройки Redis:
```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_ENABLED=true
```

### 4. Проверка подключения

Запустите Flask API и проверьте логи:
```
Redis подключён: localhost:6379
```

## 📦 Структура кэша

### Ключи кэша

```
words:list:<hash>           # Списки слов по уровням (TTL: 1 час)
words:detail:<hash>         # Детали слова (TTL: 1 час)
words:topic:<hash>          # Слова по теме (TTL: 1 час)
words:levels                # Список уровней (TTL: 24 часа)
words:topics                # Список тем (TTL: 24 часа)
words:search:<hash>         # Результаты поиска (TTL: 5 мин)

user:<id>:favorites         # Избранные слова (TTL: 5 мин)
user:<id>:trainer:words     # Слова для тренировки (TTL: 5 мин)
user:<id>:trainer:stats     # Статистика тренировки (TTL: 1 мин)
user:<id>:learning:words    # Слова в изучении (TTL: 5 мин)
user:<id>:learning:stats    # Статистика изучения (TTL: 1 мин)
```

### TTL (Time To Live)

| Тип данных | TTL | Причина |
|------------|-----|---------|
| Списки слов | 1 час | Редко меняются |
| Поиск | 5 мин | Частые новые запросы |
| Пользовательские данные | 1-5 мин | Часто обновляются |
| Статистика | 1 мин | Real-time ощущение |

## 🔄 Инвалидация кэша

Кэш автоматически инвалидируется при:

- Добавлении нового слова (`/words/custom`)
- Изменении избранного (`/words/<id>/favorite`)
- Оценке слова в тренере (`/trainer/rate`)

### Пример инвалидации

```python
@words_bp.route('/words/custom', methods=['POST'])
@token_required
@cache_invalidate('words:list:*', 'words:topics:*')
def add_custom_word():
    # ... добавление слова
    invalidate_user_cache(user_id)
```

## 🛠️ API для работы с кэшем

### Прямое управление

```python
from utils.cache_decorator import (
    get_cached_value,
    set_cached_value,
    invalidate_cache,
    invalidate_user_cache
)

# Получить значение
data = get_cached_value('words:list:abc123')

# Установить значение
set_cached_value('my:key', {'data': 'value'}, ttl=300)

# Инвалидировать ключ
invalidate_cache('my:key')

# Инвалидировать весь кэш пользователя
invalidate_user_cache(user_id=123, prefix='trainer:')
```

## 📊 Мониторинг

### Просмотр статистики Redis

```bash
redis-cli INFO stats
```

### Просмотр ключей

```bash
# Все ключи
redis-cli KEYS '*'

# Ключи по паттерну
redis-cli KEYS 'words:*'
redis-cli KEYS 'user:123:*'
```

### Размер кэша

```bash
# Количество ключей
redis-cli DBSIZE

# Использование памяти
redis-cli INFO memory
```

## ⚠️ Отладка

### Включить подробное логирование

В `.env.local`:
```env
FLASK_DEBUG=true
```

В логах вы увидите:
```
Cache HIT: words:list:abc123
Cache MISS: words:list:def456, выполняем функцию
Сохранено в кэш: words:list:def456 (TTL=3600s)
```

### Отключить кэширование

Для тестирования:
```env
REDIS_ENABLED=false
```

### Очистить весь кэш

**Development:**
```bash
redis-cli FLUSHDB
```

**Production:**
```bash
# Осторожно! Удалит все данные
redis-cli KEYS '*' | xargs redis-cli DEL
```

## 🏗️ Архитектура

```
┌─────────────┐
│  Next.js    │
│  Frontend   │
└──────┬──────┘
       │ HTTP
┌──────▼──────┐     ┌─────────────┐
│   Flask     │────▶│    Redis    │
│    API      │     │   (Cache)   │
└──────┬──────┘     └──────┬──────┘
       │                   │
       │ (cache miss)      │
┌──────▼──────┐     ┌──────▼──────┐
│ PostgreSQL  │◀────│  Invalidation │
│    (БД)     │     │   (при записи)│
└─────────────┘     └─────────────┘
```

## 📈 Эффект

### До внедрения Redis

```
GET /api/words?level=A1
→ 80-150ms
→ 1 запрос к PostgreSQL
→ 100% нагрузка на БД
```

### После внедрения Redis

```
GET /api/words?level=A1 (cache hit)
→ 5-15ms
→ 0 запросов к PostgreSQL
→ 20-40% нагрузка на БД

GET /api/words?level=A1 (cache miss)
→ 80-150ms (первый запрос)
→ 1 запрос к PostgreSQL
→ Сохранение в кэш
```

## 🔧 Конфигурация для production

### Redis Cluster

Для масштабирования:

```env
REDIS_HOST=redis-cluster.internal
REDIS_PORT=6379
REDIS_PASSWORD=secure_password
```

### Настройки памяти

В `docker-compose.yml`:
```yaml
redis:
  command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

### Мониторинг в production

Добавьте endpoint для метрик:
```python
@health_bp.route('/redis/health')
def redis_health():
    redis = get_redis_client()
    return {
        'connected': redis.enabled,
        'keys_count': redis.client.dbsize() if redis.enabled else 0
    }
```

## 📚 Дополнительные ресурсы

- [Redis Documentation](https://redis.io/docs/)
- [Redis Best Practices](https://redis.io/docs/manual/)
- [Flask Caching Patterns](https://flask.palletsprojects.com/en/2.3.x/patterns/caching/)
