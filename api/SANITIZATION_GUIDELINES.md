# Руководство по санитизации ввода данных в KlarDeutsch API

## Обзор

Этот документ описывает дополнительные меры санитизации ввода данных, реализованные поверх существующих схем Pydantic. Новые функции обеспечивают дополнительный уровень защиты от различных видов атак и некорректных данных.

## Структура санитизации

### 1. Pydantic схемы с дополнительной валидацией

Все существующие схемы в `schemas.py` были дополнены валидаторами, которые используют новые функции санитизации:

```python
from utils.sanitization_utils import (
    sanitize_string,
    sanitize_text_for_sql,
    validate_level as validate_level_func,
    validate_word_rating,
    sanitize_email as sanitize_email_func,
    sanitize_username as sanitize_username_func,
    sanitize_password as sanitize_password_func
)
```

### 2. Функции санитизации

#### sanitize_string(value: str, max_length: int = 1000) -> str
- Обрезает строку до максимальной длины
- Удаляет непечатаемые символы
- Экранирует HTML-теги
- Удаляет лишние пробелы

#### sanitize_text_for_sql(text: str) -> str
- Заменяет одинарные кавычки на экранированные (предотвращает SQL-инъекции)
- Удаляет непечатаемые символы
- Удаляет лишние пробелы

#### sanitize_html_content(content: str) -> str
- Санитизирует HTML-контент, разрешая только безопасные теги
- Использует библиотеку `bleach` для безопасной очистки

#### validate_and_sanitize_email(email: str) -> str
- Проверяет формат email с помощью регулярного выражения
- Приводит к нижнему регистру
- Возвращает пустую строку, если формат неверен

#### sanitize_username(username: str) -> str
- Проверяет длину (3-50 символов)
- Проверяет допустимые символы (буквы, цифры, подчеркивания, дефисы)
- Удаляет лишние пробелы

#### sanitize_password(password: str) -> str
- Проверяет длину (6-128 символов)
- Не изменяет содержимое, только проверяет

#### validate_level(level: str) -> bool
- Проверяет, является ли уровень одним из допустимых: A1, A2, B1, B2, C1

#### validate_word_rating(rating: int) -> bool
- Проверяет, является ли рейтинг одним из допустимых: 0, 1, 3, 5

## Обновленные схемы

### UserRegister
- Добавлены валидаторы для `username`, `email`, `password`
- Используются соответствующие функции санитизации

### WordCreate
- Добавлены валидаторы для всех текстовых полей (`de`, `ru`, `article`, `topic`, `verb_forms`, `example_de`, `example_ru`)
- Используют `sanitize_text_for_sql` и `sanitize_string`
- Добавлен валидатор для `level`

### WordSearch
- Добавлен валидатор для `query`
- Использует `sanitize_text_for_sql` и `sanitize_string`

### WordQuery
- Добавлен валидатор для `level`

### RateWordRequest
- Обновлен валидатор для `rating`, использует `validate_word_rating`

### TrainingQuery
- Добавлен валидатор для `level`

### DiaryCorrectionRequest
- Добавлен валидатор для `text`
- Использует `sanitize_text_for_sql` и `sanitize_string`

### AIEnrichRequest
- Добавлены валидаторы для `de` и `ru`
- Используют `sanitize_text_for_sql` и `sanitize_string`

## Примеры использования

### Валидация и санитизация данных пользователя:

```python
from schemas import UserRegister

try:
    user_data = UserRegister(
        username="valid_user123",
        email="user@example.com",
        password="securePassword123"
    )
    # Данные автоматически санитизированы и проверены
except ValueError as e:
    # Обработка ошибки валидации
    print(f"Ошибка валидации: {e}")
```

### Валидация и санитизация данных слова:

```python
from schemas import WordCreate

try:
    word_data = WordCreate(
        de="<script>alert('xss')</script>Haus",  # Будет санитизировано
        ru="дом",
        level="A1",
        topic="Жилье"
    )
    # Поле 'de' будет санитизировано: "<script>alert('xss')</script>Haus"
except ValueError as e:
    # Обработка ошибки валидации
    print(f"Ошибка валидации: {e}")
```

## Безопасность

### Защита от XSS
- Все текстовые поля проходят через `html.escape()`
- HTML-контент проходит через `bleach.clean()` с ограниченным набором тегов

### Защита от SQL-инъекций
- Все текстовые данные проходят через `sanitize_text_for_sql()`
- Одинарные кавычки экранируются

### Защита от переполнения
- Все строки имеют ограничения по длине
- Вложенные структуры данных имеют ограничения по глубине

## Тестирование

Для проверки работы санитизации можно использовать следующие тесты:

```python
from schemas import WordCreate

# Тестирование санитизации XSS
word = WordCreate(de="<script>alert('xss')</script>Haus", ru="дом", level="A1")
assert "<script>" not in word.de  # Должно быть заэкранировано

# Тестирование валидации уровня
try:
    word = WordCreate(de="Haus", ru="дом", level="invalid_level")
    assert False, "Должна быть ошибка валидации"
except ValueError:
    pass  # Ожидаемая ошибка

# Тестирование ограничения длины
long_text = "a" * 300  # Превышает максимальную длину
word = WordCreate(de=long_text, ru="дом", level="A1")
assert len(word.de) <= 200  # Должно быть обрезано
```

## Заключение

Добавленные функции санитизации обеспечивают дополнительный уровень безопасности поверх существующих схем Pydantic. Они помогают предотвратить XSS-атаки, SQL-инъекции и другие виды атак, связанных с некорректными пользовательскими данными. Все существующие API-эндпоинты автоматически получают выгоду от этих улучшений без необходимости изменения логики контроллеров.