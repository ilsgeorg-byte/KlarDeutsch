import os
import re
import jwt
import datetime
import bcrypt
import logging
from flask import Blueprint, request, jsonify, current_app
from functools import wraps
from db import get_db_connection, get_db_cursor
from utils.token_utils import (
    decode_token, 
    TokenError, 
    TokenExpiredError, 
    TokenInvalidError,
    TokenMissingError,
    get_token_from_header
)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Секретный ключ (в продакшене должен быть в .env.local)
# Минимальная длина для HS256: 32 байта (256 бит)
SECRET_KEY = os.environ.get("JWT_SECRET", "klardeutsch-super-secret-key-change-in-production!")

# Логгер
logger = logging.getLogger(__name__)

def is_valid_email(email):
    """Простая проверка формата email"""
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

def token_required(f):
    """
    Декоратор для обязательной авторизации
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_header()
        
        if not token:
            logger.warning("Запрос без токена авторизации")
            return jsonify({'error': 'Токен отсутствует'}), 401

        try:
            data = decode_token(token)
            # Прикрепляем user_id к запросу
            request.user_id = data['user_id']
        except TokenExpiredError:
            logger.warning("Истёкший токен авторизации")
            return jsonify({'error': 'Токен истёк'}), 401
        except TokenInvalidError as e:
            logger.warning(f"Недействительный токен: {e}")
            return jsonify({'error': 'Неверный токен'}), 401
        except TokenMissingError:
            return jsonify({'error': 'Токен отсутствует'}), 401

        return f(*args, **kwargs)

    return decorated

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not all([username, email, password]):
        logger.warning("Попытка регистрации с незаполненными полями")
        return jsonify({'error': 'Заполните все поля'}), 400

    if not is_valid_email(email):
        logger.warning(f"Попытка регистрации с неверным email: {email}")
        return jsonify({'error': 'Неверный формат email'}), 400

    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    try:
        with get_db_cursor() as cur:
            logger.info(f"Attempting to register user: {username} ({email})")
            cur.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
                (username, email, password_hash)
            )
            user_id = cur.fetchone()[0]
            logger.info(f"User registered successfully with ID: {user_id}")

            # Автоматический вход после регистрации (генерируем токен)
            token = jwt.encode({
                'user_id': user_id,
                'username': username,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
            }, SECRET_KEY, algorithm="HS256")
            logger.info(f"Generated token for new user ID: {user_id}")

            return jsonify({
                'status': 'success',
                'message': 'Пользователь зарегистрирован',
                'token': token,
                'user': {
                    'id': user_id,
                    'username': username,
                    'email': email
                }
            }), 201
    except Exception as e:
        logger.error(f"Error during user registration: {e}", exc_info=True)
        if "unique" in str(e).lower():
            return jsonify({'error': 'Такой пользователь или email уже существует'}), 400
        return jsonify({'error': 'Ошибка регистрации', 'details': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() # Используем get_json() для парсинга JSON
    email = data.get('email')
    password = data.get('password')

    logger.info(f"Received login attempt for email: {email}")

    if not all([email, password]):
        logger.warning("Login attempt with missing email or password")
        return jsonify({'error': 'Введите email и пароль'}), 400

    try:
        with get_db_cursor() as cur:
            # Используем SELECT * или конкретные столбцы, которые нужны
            cur.execute("SELECT id, username, password_hash FROM users WHERE email = %s", (email,))
            user = cur.fetchone()

            logger.info(f"Database query for email {email} returned: {user}")

            if user:
                # Убедимся, что у нас есть хэш пароля (user[2]) и он является строкой
                password_hash = user[2]
                logger.info(f"Password hash retrieved: {password_hash}. Type: {type(password_hash)}")

                if isinstance(password_hash, str):
                    # Проверяем пароль
                    if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                        logger.info(f"Password check successful for user ID: {user[0]}")
                        token = jwt.encode({
                            'user_id': user[0],
                            'username': user[1],
                            # Используем datetime.now() + timedelta для совместимости, utcnow() устарел
                            'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
                        }, SECRET_KEY, algorithm="HS256")
                        logger.info(f"Generated JWT token for user ID: {user[0]}")

                        return jsonify({
                            'token': token,
                            'user': {
                                'id': user[0],
                                'username': user[1],
                                'email': email # Возвращаем email для информации
                            }
                        }), 200
                    else:
                        logger.warning(f"Password check failed for email: {email}")
                        return jsonify({'error': 'Неверный email или пароль'}), 401
                else:
                    logger.error(f"Invalid password hash format retrieved from DB for email {email}. Expected string, got {type(password_hash)}.")
                    return jsonify({'error': 'Неверный формат хэша пароля в базе данных'}), 500
            else:
                logger.warning(f"User not found for email: {email}")
                return jsonify({'error': 'Неверный email или пароль'}), 401
    except Exception as e:
        # Логируем исключение с полным стеком для диагностики
        logger.error(f"Error during login for email {email}: {e}", exc_info=True)
        return jsonify({'error': 'Ошибка сервера при входе', 'details': str(e)}), 500

@auth_bp.route('/me', methods=['GET'])
@token_required
def get_me():
    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT id, username, email FROM users WHERE id = %s", (request.user_id,))
            user_row = cur.fetchone()

            if user_row:
                # Предполагаем, что user_row - это кортеж или объект, где user_row[0]=id, user_row[1]=username, user_row[2]=email
                return jsonify({
                    'id': user_row[0],
                    'username': user_row[1],
                    'email': user_row[2]
                }), 200
            else:
                logger.warning(f"User with ID {request.user_id} not found in DB for /me endpoint")
                return jsonify({'error': 'Пользователь не найден'}), 404
    except Exception as e:
        logger.error(f"Error fetching user data for ID {request.user_id}: {e}", exc_info=True)
        return jsonify({'error': 'Ошибка сервера при получении данных пользователя', 'details': str(e)}), 500
