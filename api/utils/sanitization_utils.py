"""
Утилиты санитизации ввода данных для KlarDeutsch API
"""

import html
import re
from typing import Union, List, Dict, Any
import bleach
from urllib.parse import urlparse


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Санитизирует строковое значение
    
    Args:
        value: Входная строка
        max_length: Максимальная длина строки
        
    Returns:
        Санитизированная строка
    """
    if not isinstance(value, str):
        raise ValueError("Значение должно быть строкой")
    
    # Обрезаем до максимальной длины
    if len(value) > max_length:
        value = value[:max_length]
    
    # Удаляем непечатаемые символы
    value = ''.join(char for char in value if ord(char) >= 32 or char in '\t\n\r')
    
    # Экранируем HTML-теги
    value = html.escape(value)
    
    return value.strip()


def sanitize_text_for_sql(text: str) -> str:
    """
    Санитизирует текст для использования в SQL-запросах
    
    Args:
        text: Входной текст
        
    Returns:
        Санитизированный текст
    """
    if not isinstance(text, str):
        return ""
    
    # Удаляем потенциально опасные символы SQL
    # Заменяем одинарные кавычки на экранированные
    text = text.replace("'", "''")
    
    # Удаляем непечатаемые символы
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\t\n\r')
    
    return text.strip()


def sanitize_html_content(content: str) -> str:
    """
    Санитизирует HTML-контент, разрешая только безопасные теги
    
    Args:
        content: HTML-контент
        
    Returns:
        Санитизированный HTML
    """
    if not isinstance(content, str):
        return ""
    
    # Разрешенные теги и атрибуты
    allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
    allowed_attributes = {}
    
    return bleach.clean(content, tags=allowed_tags, attributes=allowed_attributes, strip=True)


def validate_and_sanitize_url(url: str) -> str:
    """
    Валидирует и санитизирует URL
    
    Args:
        url: Входной URL
        
    Returns:
        Санитизированный URL или пустая строка, если недействителен
    """
    if not isinstance(url, str):
        return ""
    
    url = url.strip()
    
    if not url:
        return ""
    
    # Проверяем формат URL
    parsed = urlparse(url)
    if not all([parsed.scheme, parsed.netloc]) or parsed.scheme not in ['http', 'https']:
        return ""
    
    return url


def sanitize_user_input(data: Union[str, List, Dict[Any, Any]], max_depth: int = 3) -> Union[str, List, Dict[Any, Any]]:
    """
    Рекурсивно санитизирует пользовательский ввод
    
    Args:
        data: Входные данные (строка, список или словарь)
        max_depth: Максимальная глубина рекурсии
        
    Returns:
        Санитизированные данные
    """
    if max_depth <= 0:
        return data
    
    if isinstance(data, str):
        return sanitize_string(data)
    elif isinstance(data, list):
        return [sanitize_user_input(item, max_depth - 1) for item in data]
    elif isinstance(data, dict):
        sanitized_dict = {}
        for key, value in data.items():
            # Санитизируем только значения, не ключи
            sanitized_dict[key] = sanitize_user_input(value, max_depth - 1)
        return sanitized_dict
    else:
        return data


def validate_level(level: str) -> bool:
    """
    Валидирует уровень (A1, A2, B1, B2, C1, PERSONAL)
    
    Args:
        level: Уровень
        
    Returns:
        True если валидно, иначе False
    """
    valid_levels = {"A1", "A2", "B1", "B2", "C1", "PERSONAL"}
    return level.upper() in valid_levels


def validate_word_rating(rating: int) -> bool:
    """
    Валидирует рейтинг слова (0, 1, 3, 5)
    
    Args:
        rating: Рейтинг
        
    Returns:
        True если валидно, иначе False
    """
    return rating in [0, 1, 3, 5]


def sanitize_email(email: str) -> str:
    """
    Санитизирует и валидирует email
    
    Args:
        email: Email адрес
        
    Returns:
        Санитизированный email или пустая строка, если недействителен
    """
    if not isinstance(email, str):
        return ""
    
    email = email.strip().lower()
    
    # Простая проверка формата email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return email
    else:
        return ""


def sanitize_username(username: str) -> str:
    """
    Санитизирует имя пользователя
    
    Args:
        username: Имя пользователя
        
    Returns:
        Санитизированное имя пользователя
    """
    if not isinstance(username, str):
        raise ValueError("Имя пользователя должно быть строкой")
    
    # Удаляем пробелы в начале и конце
    username = username.strip()
    
    # Проверяем минимальную и максимальную длину
    if len(username) < 3 or len(username) > 50:
        raise ValueError("Имя пользователя должно быть от 3 до 50 символов")
    
    # Проверяем допустимые символы (буквы, цифры, подчеркивания, дефисы)
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        raise ValueError("Имя пользователя может содержать только буквы, цифры, подчеркивания и дефисы")
    
    return username


def sanitize_password(password: str) -> str:
    """
    Санитизирует пароль (не изменяет, только проверяет)
    
    Args:
        password: Пароль
        
    Returns:
        Пароль (если валиден)
        
    Raises:
        ValueError: Если пароль не соответствует требованиям
    """
    if not isinstance(password, str):
        raise ValueError("Пароль должен быть строкой")
    
    if len(password) < 6 or len(password) > 128:
        raise ValueError("Пароль должен быть от 6 до 128 символов")
    
    return password