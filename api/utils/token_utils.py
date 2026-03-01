"""
Утилиты для работы с JWT токенами
"""

import os
import jwt
import logging
from typing import Optional, Dict, Any

# Настраиваем логирование
logger = logging.getLogger(__name__)

# Секретный ключ (в продакшене должен быть в .env.local)
# Минимальная длина для HS256: 32 байта (256 бит)
SECRET_KEY = os.environ.get("JWT_SECRET", "klardeutsch-super-secret-key-change-in-production!")


class TokenError(Exception):
    """Базовое исключение для ошибок токена"""
    pass


class TokenExpiredError(TokenError):
    """Токен истёк"""
    pass


class TokenInvalidError(TokenError):
    """Токен недействителен"""
    pass


class TokenMissingError(TokenError):
    """Токен отсутствует"""
    pass


def decode_token(token: str) -> Dict[str, Any]:
    """
    Декодирует JWT токен
    
    Args:
        token: JWT токен
        
    Returns:
        Данные из токена
        
    Raises:
        TokenExpiredError: Токен истёк
        TokenInvalidError: Токен недействителен
    """
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return data
    except jwt.ExpiredSignatureError as e:
        logger.warning(f"Токен истёк: {str(e)}")
        raise TokenExpiredError("Токен истёк")
    except jwt.InvalidTokenError as e:
        logger.warning(f"Неверный токен: {str(e)}")
        raise TokenInvalidError(f"Неверный токен: {type(e).__name__}")
    except Exception as e:
        logger.error(f"Неизвестная ошибка токена: {str(e)}")
        raise TokenInvalidError(f"Ошибка токена: {str(e)}")


def get_token_from_header() -> Optional[str]:
    """
    Извлекает токен из заголовка Authorization
    
    Returns:
        Токен или None, если заголовок отсутствует
    """
    from flask import request
    
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    
    if not auth_header.startswith('Bearer '):
        logger.warning(f"Неверный формат Authorization: {auth_header[:10]}...")
        return None
    
    return auth_header.split(" ")[1]


def get_current_user_id_optional() -> Optional[int]:
    """
    Безопасно получает user_id из токена (опционально)
    
    Используется в endpoints, где авторизация не обязательна,
    но желательна для персонализации ответов.
    
    Returns:
        user_id если токен валиден, иначе None
    """
    from flask import request
    
    token = get_token_from_header()
    if not token:
        return None
    
    try:
        data = decode_token(token)
        return data.get('user_id')
    except TokenError as e:
        # Логирование уже выполнено в decode_token
        return None


def get_current_user_id_required() -> int:
    """
    Получает user_id из токена (обязательно)
    
    Используется в endpoints, где авторизация обязательна.
    
    Returns:
        user_id
        
    Raises:
        TokenMissingError: Токен не предоставлен
        TokenExpiredError: Токен истёк
        TokenInvalidError: Токен недействителен
    """
    from flask import request
    
    token = get_token_from_header()
    if not token:
        logger.warning("Токен отсутствует в запросе")
        raise TokenMissingError("Токен отсутствует")
    
    data = decode_token(token)
    return data['user_id']
