"""
KlarDeutsch API - приложение для изучения немецкого языка
Основное приложение Flask с подключением маршрутов
"""
from flask import Flask, jsonify, g
from flask_cors import CORS
import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Добавляем текущую директорию в path для импортов
sys.path.insert(0, os.path.dirname(__file__))

# Загружаем переменные окружения ОДИН РАЗ в точке входа
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.local')
load_dotenv(env_path)
logger.info("Environment variables loaded from .env.local")

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
        "methods": ["GET", "POST", "OPTIONS", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Регистрируем blueprints (маршруты)
try:
    from routes.words import words_bp
    from routes.audio import audio_bp
    from routes.diary import diary_bp
    from routes.trainer import trainer_bp
    from routes.auth import auth_bp
    from routes.ai_enrich import ai_enrich_bp
    from db import init_db
except ImportError:
    from .routes.words import words_bp
    from .routes.audio import audio_bp
    from .routes.diary import diary_bp
    from .routes.trainer import trainer_bp
    from .routes.auth import auth_bp
    from .routes.ai_enrich import ai_enrich_bp
    from .db import init_db

# Инициализируем базу данных (создаем таблицы если их нет)
init_db()

app.register_blueprint(words_bp)
app.register_blueprint(audio_bp)
app.register_blueprint(diary_bp)
app.register_blueprint(trainer_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(ai_enrich_bp)


# === Управление соединением с БД на уровне запроса ===

@app.before_request
def before_request():
    """Логирование запроса и подготовка (опционально)"""
    if app.debug:
        logger.debug(f"{request.method} {request.path}")


@app.teardown_request
def teardown_request(exception=None):
    """
    Очистка после запроса (если нужно)
    psycopg2 сам закрывает соединения при сборке мусора,
    но можно добавить дополнительную логику
    """
    if exception:
        logger.error(f"Request failed with exception: {exception}")


# Логирование запросов
from flask import request

@app.before_request
def log_request():
    """Логирование входящих запросов"""
    logger.info(f"[{datetime.now()}] {request.method} {request.path}")


# Health check endpoint
@app.route('/health', methods=['GET'])
def health():
    """Проверка состояния сервера"""
    return jsonify({"status": "ok"}), 200


# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Обработка ошибки 404"""
    logger.warning(f"404: {request.path}")
    return jsonify({"error": "Endpoint не найден"}), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Обработка ошибки 405"""
    logger.warning(f"405: {request.method} {request.path}")
    return jsonify({"error": "Метод не поддерживается"}), 405


@app.errorhandler(500)
def internal_error(error):
    """Обработка ошибки 500"""
    import traceback
    logger.error(f"500 Error: {str(error)}")
    logger.error(traceback.format_exc())
    return jsonify({"error": "Внутренняя ошибка сервера", "details": str(error)}), 500

