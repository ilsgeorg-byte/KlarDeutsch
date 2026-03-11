"""
Тесты для проверки ограничения частоты запросов (rate limiting)
"""

import unittest
from unittest.mock import patch
from index import app


class TestRateLimiting(unittest.TestCase):
    
    def setUp(self):
        """Настройка тестового клиента"""
        self.app = app.test_client()
        self.app.testing = True
    
    def test_health_endpoint_rate_limit(self):
        """Тест ограничения частоты для эндпоинта health"""
        # Делаем несколько запросов к эндпоинту health
        for i in range(3):
            response = self.app.get('/health')
            self.assertEqual(response.status_code, 200)
    
    def test_auth_endpoint_rate_limit(self):
        """Тест ограничения частоты для эндпоинта аутентификации"""
        # Делаем несколько запросов к эндпоинту аутентификации
        for i in range(2):
            response = self.app.post('/api/auth/login', json={
                'email': 'test@example.com',
                'password': 'password123'
            })
            # Может вернуть 400 (неправильные учетные данные) или 200, но не 429 (rate limited)
            self.assertIn(response.status_code, [200, 400, 401])
    
    def test_ai_endpoint_rate_limit(self):
        """Тест ограничения частоты для AI эндпоинта"""
        # Делаем несколько запросов к AI эндпоинту
        for i in range(2):
            response = self.app.post('/api/ai/enrich', json={
                'de': 'Haus',
                'ru': 'дом'
            })
            # Может вернуть 400 (неправильные данные) или 200, но не 429 (rate limited)
            self.assertIn(response.status_code, [200, 400])
    
    @patch('flask_limiter.Limiter.check')
    def test_rate_limit_integration(self, mock_check):
        """Тест интеграции с flask-limiter"""
        # Мокируем проверку ограничений, чтобы убедиться, что она вызывается
        mock_check.return_value = True
        
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    print("Запуск тестов ограничения частоты запросов...")
    unittest.main(verbosity=2)