"""
Redis клиент для KlarDeutsch

Единый экземпляр Redis с поддержкой кэширования и fallback на БД
"""

import os
import json
import logging
from typing import Any, Optional
from contextlib import contextmanager

import redis
from redis.exceptions import RedisError, ConnectionError, TimeoutError

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Обёртка над Redis клиентом с обработкой ошибок и логированием
    """

    def __init__(self):
        self._client: Optional[redis.Redis] = None
        self._enabled = False
        self._init_client()

    def _init_client(self):
        """Инициализация Redis клиента"""
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        redis_password = os.getenv('REDIS_PASSWORD', None)
        redis_db = int(os.getenv('REDIS_DB', 0))
        redis_enabled = os.getenv('REDIS_ENABLED', 'true').lower() == 'true'

        if not redis_enabled:
            logger.info("Redis отключён (REDIS_ENABLED=false)")
            return

        try:
            self._client = redis.Redis(
                host=redis_host,
                port=redis_port,
                password=redis_password,
                db=redis_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )

            # Проверяем соединение
            self._client.ping()
            self._enabled = True
            logger.info(f"Redis подключён: {redis_host}:{redis_port}")

        except (ConnectionError, TimeoutError) as e:
            logger.warning(f"Не удалось подключиться к Redis: {e}. Кэширование отключено, fallback на БД.")
            self._client = None
            self._enabled = False
        except Exception as e:
            logger.error(f"Ошибка инициализации Redis: {e}. Кэширование отключено.")
            self._client = None
            self._enabled = False

    @property
    def enabled(self) -> bool:
        """Проверка доступности Redis"""
        return self._enabled

    @property
    def client(self) -> Optional[redis.Redis]:
        """Получение Redis клиента"""
        return self._client

    def get(self, key: str) -> Optional[Any]:
        """
        Получение значения из кэша

        Args:
            key: Ключ кэша

        Returns:
            Значение или None если не найдено/ошибка
        """
        if not self._enabled or not self._client:
            return None

        try:
            value = self._client.get(key)
            if value:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(value)
            logger.debug(f"Cache MISS: {key}")
            return None
        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Ошибка чтения из Redis: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Сохранение значения в кэш

        Args:
            key: Ключ кэша
            value: Значение (сериализуется в JSON)
            ttl: Время жизни в секундах (опционально)

        Returns:
            True если успешно, False если ошибка
        """
        if not self._enabled or not self._client:
            return False

        try:
            serialized = json.dumps(value, ensure_ascii=False)
            if ttl:
                self._client.setex(key, ttl, serialized)
            else:
                self._client.set(key, serialized)
            logger.debug(f"Cache SET: {key} (TTL={ttl})")
            return True
        except (RedisError, TypeError) as e:
            logger.error(f"Ошибка записи в Redis: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Удаление ключа из кэша

        Args:
            key: Ключ для удаления

        Returns:
            True если удалён, False если ошибка
        """
        if not self._enabled or not self._client:
            return False

        try:
            result = self._client.delete(key)
            logger.debug(f"Cache DELETE: {key} (removed {result} keys)")
            return result > 0
        except RedisError as e:
            logger.error(f"Ошибка удаления из Redis: {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        Удаление ключей по паттерну

        Args:
            pattern: Паттерн ключей (например, 'words:*')

        Returns:
            Количество удалённых ключей
        """
        if not self._enabled or not self._client:
            return 0

        try:
            keys = self._client.keys(pattern)
            if keys:
                result = self._client.delete(*keys)
                logger.debug(f"Cache DELETE PATTERN: {pattern} (removed {result} keys)")
                return result
            return 0
        except RedisError as e:
            logger.error(f"Ошибка удаления по паттерну из Redis: {e}")
            return 0

    def invalidate(self, *keys: str) -> bool:
        """
        Инвалидация нескольких ключей

        Args:
            keys: Ключи для инвалидации

        Returns:
            True если все удалены успешно
        """
        if not self._enabled or not self._client:
            return False

        success = True
        for key in keys:
            if not self.delete(key):
                success = False
        return success

    def flush_db(self) -> bool:
        """
        Очистка всей базы данных Redis

        WARNING: Используйте только в development!

        Returns:
            True если успешно
        """
        if not self._enabled or not self._client:
            return False

        env = os.getenv('FLASK_ENV', 'development')
        if env != 'development':
            logger.warning(f"Попытка FLUSHDB в {env} среде отклонена")
            return False

        try:
            self._client.flushdb()
            logger.warning("Redis DB очищен (development mode)")
            return True
        except RedisError as e:
            logger.error(f"Ошибка очистки Redis: {e}")
            return False


# Глобальный экземпляр
redis_client = RedisClient()


def get_redis_client() -> RedisClient:
    """Получение глобального экземпляра Redis клиента"""
    return redis_client


@contextmanager
def redis_lock(lock_name: str, timeout: int = 10):
    """
    Контекстный менеджер для распределённой блокировки

    Использование:
        with redis_lock('my_lock'):
            # критическая секция

    Args:
        lock_name: Имя блокировки
        timeout: Таймаут в секундах
    """
    client = get_redis_client()
    lock = None

    if client.enabled and client.client:
        try:
            lock = client.client.lock(lock_name, timeout=timeout)
            acquired = lock.acquire(blocking=True, blocking_timeout=timeout)
            if acquired:
                logger.debug(f"Lock acquired: {lock_name}")
                yield True
                lock.release()
                logger.debug(f"Lock released: {lock_name}")
            else:
                logger.warning(f"Lock timeout: {lock_name}")
                yield False
        except RedisError as e:
            logger.error(f"Lock error: {e}")
            yield False
    else:
        # Redis недоступен - выполняем без блокировки
        yield True
