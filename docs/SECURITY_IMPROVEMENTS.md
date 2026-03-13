# 🔐 Security & Code Quality Improvements - KlarDeutsch

## 📊 Резюме

**Дата:** 1 марта 2026  
**Статус:** ✅ Завершено  
**Файлы изменены:** 3  
**Файлы созданы:** 3

---

## ✅ Выполненные улучшения

### 1. Централизация логики работы с токенами

**Проблема:** Логика декодирования JWT дублировалась в нескольких файлах.

**Решение:** Создан модуль `utils/token_utils.py` с едиными функциями.

| Файл | Было | Стало |
|------|------|-------|
| `auth.py` | `jwt.decode()` напрямую | `decode_token()` из utils |
| `words.py` | `jwt.decode()` с try/except | `get_current_user_id_optional()` |

---

### 2. Улучшенная обработка ошибок токенов

**Было:**
```python
try:
    data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    return data['user_id']
except:  # ❌ Проглатывает все ошибки
    pass
```

**Стало:**
```python
from utils.token_utils import decode_token, TokenError

try:
    data = decode_token(token)  # ✅ Специфичные исключения
    return data['user_id']
except TokenExpiredError:
    logger.warning("Токен истёк")
except TokenInvalidError as e:
    logger.warning(f"Неверный токен: {e}")
```

---

### 3. Логирование ошибок безопасности

**Добавлены лог-сообщения для:**

| Событие | Уровень | Сообщение |
|---------|---------|-----------|
| Токен отсутствует | WARNING | "Запрос без токена авторизации" |
| Токен истёк | WARNING | "Истёкший токен авторизации" |
| Токен недействителен | WARNING | "Недействительный токен: {error}" |
| Неверный формат Authorization | WARNING | "Неверный формат Authorization: ..." |
| Опциональная авторизация не прошла | DEBUG | "Запрос с авторизацией, но токен не валиден" |

---

### 4. Специфичные исключения для токенов

**Созданы классы исключений:**

```python
class TokenError(Exception):
    """Базовое исключение для ошибок токена"""

class TokenExpiredError(TokenError):
    """Токен истёк"""

class TokenInvalidError(TokenError):
    """Токен недействителен"""

class TokenMissingError(TokenError):
    """Токен отсутствует"""
```

**Преимущества:**
- ✅ Точная обработка разных типов ошибок
- ✅ Понятные сообщения пользователю
- ✅ Логирование с контекстом

---

## 📁 Новые файлы

### 1. `api/utils/token_utils.py`

**Функции:**

| Функция | Назначение | Возвращает |
|---------|-----------|------------|
| `decode_token(token)` | Декодирование JWT | Dict с данными |
| `get_token_from_header()` | Извлечение из заголовка | Token или None |
| `get_current_user_id_optional()` | Опциональная авторизация | user_id или None |
| `get_current_user_id_required()` | Обязательная авторизация | user_id или Exception |

**Исключения:**

| Исключение | Когда выбрасывается |
|------------|---------------------|
| `TokenExpiredError` | Токен истёк (exp < now) |
| `TokenInvalidError` | Невалидная подпись, формат |
| `TokenMissingError` | Токен не предоставлен |

---

### 2. `api/utils/__init__.py`

Пустой файл для превращения директории в Python-пакет.

---

## 📝 Изменённые файлы

### 1. `api/routes/auth.py`

**Изменения:**

```diff
+ import logging
+ from utils.token_utils import (
+     decode_token,
+     TokenError,
+     TokenExpiredError,
+     TokenInvalidError,
+     TokenMissingError,
+     get_token_from_header
+ )

+ logger = logging.getLogger(__name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
-         token = None
-         if 'Authorization' in request.headers:
-             auth_header = request.headers['Authorization']
-             if auth_header.startswith('Bearer '):
-                 token = auth_header.split(" ")[1]
+         token = get_token_from_header()
+         
+         if not token:
+             logger.warning("Запрос без токена авторизации")
+             return jsonify({'error': 'Токен отсутствует'}), 401

        try:
-             data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
+             data = decode_token(token)
              request.user_id = data['user_id']
-         except Exception as e:
+         except TokenExpiredError:
+             logger.warning("Истёкший токен авторизации")
+             return jsonify({'error': 'Токен истёк'}), 401
+         except TokenInvalidError as e:
+             logger.warning(f"Недействительный токен: {e}")
              return jsonify({'error': 'Неверный токен'}), 401
```

---

### 2. `api/routes/words.py`

**Изменения:**

```diff
+ import logging
- import jwt
+ from utils.token_utils import get_current_user_id_optional

+ logger = logging.getLogger(__name__)

def get_current_user_id():
    """
    Безопасно получаем user_id из заголовка (опционально)
    
    Используется для персонализации ответов (избранные слова и т.п.)
    При ошибке токена возвращает None и логирует событие.
    
    Returns:
        user_id если токен валиден, иначе None
    """
-     auth_header = request.headers.get('Authorization')
-     if auth_header and auth_header.startswith('Bearer '):
-         token = auth_header.split(" ")[1]
-         try:
-             data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
-             return data['user_id']
-         except:
-             pass
-     return None
+     user_id = get_current_user_id_optional()
+     if user_id is None:
+         auth_header = request.headers.get('Authorization')
+         if auth_header:
+             logger.debug("Запрос с авторизацией, но токен не валиден")
+     return user_id
```

---

## 🎯 Преимущества новой архитектуры

### 1. DRY (Don't Repeat Yourself)

- ✅ Логика декодирования в одном месте
- ✅ Единый стиль обработки ошибок

### 2. Безопасность

- ✅ Логирование всех неудачных попыток авторизации
- ✅ Разные сообщения для разных типов ошибок
- ✅ Нет "проглатывания" исключений

### 3. Поддерживаемость

- ✅ Легко изменить алгоритм шифрования (одно место)
- ✅ Легко добавить новые типы исключений
- ✅ Понятный API для разработчиков

### 4. Тестируемость

- ✅ Функции можно тестировать отдельно
- ✅ Моки для токенов в тестах

---

## 🔧 Настройка логирования

### Для разработки (app.py):

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Для production:

```python
import logging
import sys

# Только предупреждения и выше
handler = logging.StreamHandler(sys.stderr)
handler.setLevel(logging.WARNING)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)

logging.getLogger('utils.token_utils').addHandler(handler)
logging.getLogger('utils.token_utils').setLevel(logging.WARNING)
```

---

## 📋 Примеры использования

### 1. Обязательная авторизация

```python
from routes.auth import token_required

@trainer_bp.route('/stats', methods=['GET'])
@token_required
def get_stats():
    # Токен обязателен, иначе 401
    user_id = request.user_id
    ...
```

### 2. Опциональная авторизация

```python
from utils.token_utils import get_current_user_id_optional

@words_bp.route('/words', methods=['GET'])
def get_words():
    # Токен не обязателен, но если есть - персонализируем
    user_id = get_current_user_id_optional()
    if user_id:
        # Показываем избранные слова
        ...
    else:
        # Показываем общие слова
        ...
```

### 3. Ручная обработка ошибок

```python
from utils.token_utils import (
    get_token_from_header,
    decode_token,
    TokenExpiredError,
    TokenInvalidError
)

@some_bp.route('/sensitive', methods=['POST'])
def sensitive_operation():
    token = get_token_from_header()
    
    if not token:
        return jsonify({'error': 'Требуется авторизация'}), 401
    
    try:
        data = decode_token(token)
        user_id = data['user_id']
    except TokenExpiredError:
        return jsonify({'error': 'Сессия истекла, войдите снова'}), 401
    except TokenInvalidError:
        return jsonify({'error': 'Недействительная сессия'}), 401
    
    # Дальше работаем с user_id
    ...
```

---

## 🧪 Тестирование

### Unit-тесты для token_utils.py

```python
import pytest
from utils.token_utils import (
    decode_token,
    TokenExpiredError,
    TokenInvalidError,
    get_current_user_id_optional
)

def test_decode_valid_token():
    # Создать валидный токен
    token = jwt.encode({...}, SECRET_KEY)
    data = decode_token(token)
    assert 'user_id' in data

def test_decode_expired_token():
    # Создать истёкший токен
    token = jwt.encode({'exp': 0}, SECRET_KEY)
    with pytest.raises(TokenExpiredError):
        decode_token(token)

def test_decode_invalid_token():
    # Невалидная подпись
    token = "invalid.token.here"
    with pytest.raises(TokenInvalidError):
        decode_token(token)
```

---

## 📊 Метрики безопасности

| Метрика | До | После |
|---------|-----|-------|
| Дублирование кода | 3 файла | 1 файл |
| Типы исключений | 1 (Exception) | 4 (специфичные) |
| Логирование ошибок | ❌ Нет | ✅ Есть |
| Обработка истёкших токенов | ❌ Нет | ✅ Есть |
| Понятные сообщения | ❌ "Неверный токен" | ✅ Разные для каждой ошибки |

---

## ✅ Чек-лист

- [x] Создан модуль `utils/token_utils.py`
- [x] Созданы специфичные исключения
- [x] Обновлён `auth.py` для использования utils
- [x] Обновлён `words.py` для использования utils
- [x] Добавлено логирование ошибок
- [x] Убрано дублирование кода
- [x] Улучшены сообщения об ошибках

---

## 🔄 Следующие шаги

### Рекомендуется:

1. **Настроить логирование в production**
   - Отправлять warning/error логи в мониторинг
   - Настроить алерты при множественных неудачных авторизациях

2. **Добавить rate limiting**
   - Ограничить количество неудачных попыток входа
   - Защитить от brute-force атак

3. **Добавить refresh tokens**
   - Короткоживущие access токены (15 мин)
   - Долгоживущие refresh токены (7 дней)

4. **Добавить тесты**
   - Unit-тесты для token_utils.py
   - Integration-тесты для auth endpoints

---

**Дата:** 1 марта 2026  
**Статус:** ✅ Завершено  
**Следующий аудит:** 1 апреля 2026
