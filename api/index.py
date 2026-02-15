"""
KlarDeutsch API - приложение для изучения немецкого языка
Основное приложение Flask с подключением маршрутов
"""
from flask import Flask, jsonify
from flask_cors import CORS
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Загружаем переменные окружения
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.local')
load_dotenv(env_path)

# Инициализируем Flask приложение
app = Flask(__name__)

# Настройка CORS
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://127.0.0.1:3000",
            "http://localhost:3000",
            "http://127.0.0.1:5000",
            "localhost:3000",
            "https://klar-deutsch.vercel.app"
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Регистрируем blueprints (маршруты)
from routes.words import words_bp
from routes.audio import audio_bp

app.register_blueprint(words_bp)
app.register_blueprint(audio_bp)

# Health check endpoint
@app.route('/health', methods=['GET'])
def health():
    """Проверка состояния сервера"""
    return jsonify({"status": "ok"}), 200

# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Обработка ошибки 404"""
    return jsonify({"error": "Endpoint не найден"}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """Обработка ошибки 405"""
    return jsonify({"error": "Метод не поддерживается"}), 405

@app.errorhandler(500)
def internal_error(error):
    """Обработка ошибки 500"""
    return jsonify({"error": "Внутренняя ошибка сервера"}), 500

# Логирование запросов
from flask import request

@app.before_request
def log_request():
    """Логирование входящих запросов"""
    if app.debug:
        print(f"[{datetime.now()}] {request.method} {request.path}")



if __name__ == "__main__":
    app.run(debug=True)

