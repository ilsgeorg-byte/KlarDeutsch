"""
Декораторы для кэширования ответов API

Использование:
    @cache_response('words:list', ttl=3600)
    def get_words():
        ...
"""

import hashlib
import logging
from functools import wraps
from typing import Optional, Callable

from flask import request, jsonify
from .redis_client import get_redis_client

logger = logging.getLogger(__name__)


def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Генерация уникального ключа кэша на основе параметров запроса

    Args:
        prefix: Префикс ключа (например, 'words:list')
        *args: Позиционные аргументы
        **kwargs: Именованные аргументы

    Returns:
        Строка ключа в формате 'prefix:hash'
    """
    # Собираем все данные для хэша
    key_data = {
        'args': args,
        'kwargs': sorted(kwargs.items()),
        'query_params': sorted(request.args.to_dict().items()) if request else None,
    }

    # Создаём хэш
    key_string = str(key_data)
    hash_value = hashlib.md5(key_string.encode('utf-8')).hexdigest()[:12]

    return f"{prefix}:{hash_value}"


def cache_response(prefix: str, ttl: int = 300, user_specific: bool = False):
    """
    Декоратор для кэширования ответов Flask API

    Args:
        prefix: Префикс ключа кэша (например, 'words:list')
        ttl: Время жизни кэша в секундах (по умолчанию 300 = 5 мин)
        user_specific: Если True, добавляет user_id к ключу (для пользовательских данных)

    Returns:
        Декорированная функция

    Пример использования:
        @words_bp.route('/words', methods=['GET'])
        @cache_response('words:list', ttl=3600)
        def get_words():
            ...

        @trainer_bp.route('/words', methods=['GET'])
        @cache_response('trainer:words', ttl=300, user_specific=True)
        def get_training_words():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            redis = get_redis_client()

            # Если Redis недоступен, выполняем функцию без кэширования
            if not redis.enabled:
                logger.debug(f"Redis недоступен, выполняем {func.__name__} без кэширования")
                return func(*args, **kwargs)

            # Формируем ключ кэша
            cache_key = generate_cache_key(prefix, *args, **kwargs)

            # Добавляем user_id для пользовательских данных
            if user_specific:
                user_id = getattr(request, 'user_id', None)
                if user_id:
                    cache_key = f"user:{user_id}:{cache_key}"
                else:
                    # Нет авторизации - используем анонимный ключ
                    cache_key = f"anon:{cache_key}"

            # Пробуем получить из кэша
            cached_data = redis.get(cache_key)
            if cached_data is not None:
                logger.info(f"Cache HIT: {cache_key}")
                return jsonify(cached_data), 200

            # Кэш не найден - выполняем функцию
            logger.info(f"Cache MISS: {cache_key}, выполняем функцию")
            response = func(*args, **kwargs)

            # Сохраняем результат в кэш
            try:
                # Получаем данные из ответа Flask
                if isinstance(response, tuple):
                    data, status_code = response[0], response[1] if len(response) > 1 else 200
                else:
                    data, status_code = response, 200

                # Кэшируем только успешные ответы
                if status_code == 200:
                    if hasattr(data, 'get_json'):
                        json_data = data.get_json()
                    else:
                        json_data = data

                    if json_data is not None:
                        redis.set(cache_key, json_data, ttl=ttl)
                        logger.debug(f"Сохранено в кэш: {cache_key} (TTL={ttl}s)")
            except Exception as e:
                logger.error(f"Ошибка кэширования ответа {func.__name__}: {e}")

            return response

        return wrapper
    return decorator


def cache_invalidate(*patterns: str):
    """
    Декоратор для инвалидации кэша после операций записи

    Args:
        *patterns: Паттерны ключей для инвалидации (например, 'words:*', 'user:123:trainer:*')

    Returns:
        Декорированная функция

    Пример использования:
        @words_bp.route('/words/custom', methods=['POST'])
        @token_required
        @cache_invalidate('words:list:*', 'topics:*')
        def add_custom_word():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Выполняем функцию
            response = func(*args, **kwargs)

            # Инвалидируем кэш после успешной операции
            try:
                status_code = response[1] if isinstance(response, tuple) and len(response) > 1 else 200
                if status_code in (200, 201):
                    redis = get_redis_client()
                    if redis.enabled:
                        for pattern in patterns:
                            # Заменяем * на реальный паттерн Redis
                            redis_pattern = pattern.replace('*', '*')
                            deleted = redis.delete_pattern(redis_pattern)
                            logger.info(f"Инвалидировано кэшей по паттерну '{pattern}': {deleted}")
            except Exception as e:
                logger.error(f"Ошибка инвалидации кэша в {func.__name__}: {e}")

            return response

        return wrapper
    return decorator


def get_cached_value(key: str) -> Optional[any]:
    """
    Прямое получение значения из кэша

    Args:
        key: Ключ кэша

    Returns:
        Значение или None
    """
    redis = get_redis_client()
    return redis.get(key) if redis.enabled else None


def set_cached_value(key: str, value: any, ttl: int = 300) -> bool:
    """
    Прямая запись значения в кэш

    Args:
        key: Ключ кэша
        value: Значение
        ttl: Время жизни в секундах

    Returns:
        True если успешно
    """
    redis = get_redis_client()
    return redis.set(key, value, ttl=ttl) if redis.enabled else False


def invalidate_cache(*keys: str) -> bool:
    """
    Инвалидация конкретных ключей кэша

    Args:
        *keys: Ключи для удаления

    Returns:
        True если все удалены успешно
    """
    redis = get_redis_client()
    if not redis.enabled:
        return False

    success = True
    for key in keys:
        if not redis.delete(key):
            success = False
    return success


def invalidate_user_cache(user_id: int, prefix: Optional[str] = None) -> int:
    """
    Инвалидация всего кэша пользователя

    Args:
        user_id: ID пользователя
        prefix: Опциональный префикс для фильтрации

    Returns:
        Количество удалённых ключей
    """
    redis = get_redis_client()
    if not redis.enabled:
        return 0

    pattern = f"user:{user_id}:{prefix}*" if prefix else f"user:{user_id}:*"
    return redis.delete_pattern(pattern)
