"""
Тесты для функций санитизации ввода данных
"""

import unittest
from utils.sanitization_utils import (
    sanitize_string,
    sanitize_text_for_sql,
    sanitize_html_content,
    validate_level,
    validate_word_rating,
    sanitize_email,
    sanitize_username,
    sanitize_password,
    sanitize_user_input
)
from schemas import UserRegister, WordCreate, WordSearch, RateWordRequest


class TestSanitizationUtils(unittest.TestCase):
    
    def test_sanitize_string(self):
        """Тест санитизации строк"""
        # Простая строка
        result = sanitize_string("hello world")
        self.assertEqual(result, "hello world")
        
        # Строка с HTML-тегами
        result = sanitize_string("<script>alert('xss')</script>")
        self.assertEqual(result, "<script>alert('xss')</script>")
        
        # Строка с лишними пробелами
        result = sanitize_string("  hello   world  ")
        self.assertEqual(result, "hello   world")
        
        # Строка, превышающая максимальную длину
        long_str = "a" * 1500
        result = sanitize_string(long_str, max_length=100)
        self.assertEqual(len(result), 100)
        
        # Строка с непечатаемыми символами
        result = sanitize_string("hello\x00world\t\n")
        self.assertEqual(result, "hello\t\nworld\t\n")
    
    def test_sanitize_text_for_sql(self):
        """Тест санитизации текста для SQL"""
        # Простой текст
        result = sanitize_text_for_sql("hello world")
        self.assertEqual(result, "hello world")
        
        # Текст с одинарными кавычками
        result = sanitize_text_for_sql("don't stop")
        self.assertEqual(result, "don''t stop")
        
        # Текст с непечатаемыми символами
        result = sanitize_text_for_sql("hello\x00world")
        self.assertEqual(result, "helloworld")
    
    def test_sanitize_html_content(self):
        """Тест санитизации HTML-контента"""
        # Разрешенные теги
        result = sanitize_html_content("<p>Hello <strong>world</strong></p>")
        self.assertEqual(result, "<p>Hello <strong>world</strong></p>")
        
        # Запрещенные теги
        result = sanitize_html_content("<p>Hello <script>alert('xss')</script> world</p>")
        self.assertEqual(result, "<p>Hello alert('xss') world</p>")
    
    def test_validate_level(self):
        """Тест валидации уровня"""
        self.assertTrue(validate_level("A1"))
        self.assertTrue(validate_level("C1"))
        self.assertFalse(validate_level("invalid"))
        self.assertFalse(validate_level("A0"))
    
    def test_validate_word_rating(self):
        """Тест валидации рейтинга слова"""
        self.assertTrue(validate_word_rating(0))
        self.assertTrue(validate_word_rating(1))
        self.assertTrue(validate_word_rating(3))
        self.assertTrue(validate_word_rating(5))
        self.assertFalse(validate_word_rating(2))
        self.assertFalse(validate_word_rating(4))
        self.assertFalse(validate_word_rating(6))
    
    def test_sanitize_email(self):
        """Тест санитизации email"""
        # Валидный email
        result = sanitize_email("user@example.com")
        self.assertEqual(result, "user@example.com")
        
        # Валидный email в верхнем регистре
        result = sanitize_email("USER@EXAMPLE.COM")
        self.assertEqual(result, "user@example.com")
        
        # Невалидный email
        result = sanitize_email("invalid-email")
        self.assertEqual(result, "")
        
        # Email без домена
        result = sanitize_email("user@")
        self.assertEqual(result, "")
    
    def test_sanitize_username(self):
        """Тест санитизации имени пользователя"""
        # Валидное имя пользователя
        result = sanitize_username("valid_user123")
        self.assertEqual(result, "valid_user123")
        
        # Имя пользователя с лишними пробелами (должно пройти, так как strip() удаляет пробелы)
        result = sanitize_username("  user123  ")
        self.assertEqual(result, "user123")
        
        # Слишком короткое имя
        with self.assertRaises(ValueError):
            sanitize_username("ab")
        
        # Слишком длинное имя
        with self.assertRaises(ValueError):
            sanitize_username("a" * 51)
        
        # Имя с недопустимыми символами
        with self.assertRaises(ValueError):
            sanitize_username("user@name")
    
    def test_sanitize_password(self):
        """Тест санитизации пароля"""
        # Валидный пароль
        result = sanitize_password("validPass123")
        self.assertEqual(result, "validPass123")
        
        # Слишком короткий пароль
        with self.assertRaises(ValueError):
            sanitize_password("short")
        
        # Слишком длинный пароль
        with self.assertRaises(ValueError):
            sanitize_password("a" * 129)
    
    def test_sanitize_user_input(self):
        """Тест рекурсивной санитизации пользовательского ввода"""
        # Простая строка
        result = sanitize_user_input("hello world")
        self.assertEqual(result, "hello world")
        
        # Список строк
        result = sanitize_user_input(["hello", "<script>xss</script>"])
        self.assertEqual(result, ["hello", "<script>xss</script>"])
        
        # Словарь
        result = sanitize_user_input({
            "name": "John",
            "bio": "<script>alert('xss')</script>"
        })
        self.assertEqual(result, {
            "name": "John",
            "bio": "<script>alert('xss')</script>"
        })
        
        # Вложенный словарь
        result = sanitize_user_input({
            "user": {
                "name": "Jane",
                "bio": "<p>Safe bio</p>"
            }
        })
        self.assertEqual(result, {
            "user": {
                "name": "Jane",
                "bio": "<p>Safe bio</p>"
            }
        })


class TestPydanticSchemaValidation(unittest.TestCase):
    
    def test_user_register_validation(self):
        """Тест валидации схемы регистрации пользователя"""
        # Валидные данные
        user = UserRegister(
            username="testuser123",
            email="test@example.com",
            password="securePassword123"
        )
        self.assertEqual(user.username, "testuser123")
        self.assertEqual(user.email, "test@example.com")
        
        # Невалидный email
        with self.assertRaises(ValueError):
            UserRegister(
                username="testuser",
                email="invalid-email",
                password="password123"
            )
        
        # Невалидное имя пользователя
        with self.assertRaises(ValueError):
            UserRegister(
                username="us",  # Слишком короткое
                email="test@example.com",
                password="password123"
            )
    
    def test_word_create_validation(self):
        """Тест валидации схемы создания слова"""
        # Валидные данные
        word = WordCreate(
            de="Haus",
            ru="дом",
            level="A1",
            topic="Жилье"
        )
        self.assertEqual(word.de, "Haus")
        self.assertEqual(word.level, "A1")
        
        # Невалидный уровень
        with self.assertRaises(ValueError):
            WordCreate(
                de="Haus",
                ru="дом",
                level="invalid",
                topic="Жилье"
            )
        
        # XSS в поле de
        word = WordCreate(
            de="<script>alert('xss')</script>Haus",
            ru="дом",
            level="A1",
            topic="Жилье"
        )
        # Проверяем, что скрипт был заэкранирован
        self.assertIn("<script>", word.de)
        self.assertNotIn("<script>", word.de)
    
    def test_word_search_validation(self):
        """Тест валидации схемы поиска слов"""
        # Валидные данные
        search = WordSearch(query="haus", limit=10)
        self.assertEqual(search.query, "haus")
        
        # XSS в поисковом запросе
        search = WordSearch(query="<script>alert('xss')</script>", limit=10)
        # Проверяем, что скрипт был заэкранирован
        self.assertIn("<script>", search.query)
        self.assertNotIn("<script>", search.query)
    
    def test_rate_word_request_validation(self):
        """Тест валидации схемы оценки слова"""
        # Валидные данные
        rating = RateWordRequest(word_id=1, rating=3)
        self.assertEqual(rating.rating, 3)
        
        # Невалидный рейтинг
        with self.assertRaises(ValueError):
            RateWordRequest(word_id=1, rating=2)  # 2 не входит в допустимые значения


if __name__ == '__main__':
    print("Запуск тестов санитизации...")
    unittest.main(verbosity=2)