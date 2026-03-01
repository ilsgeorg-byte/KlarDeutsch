import os
import re
import jwt
import datetime
import bcrypt
import logging
from flask import Blueprint, request, jsonify, current_app
from functools import wraps
from db import get_db_connection
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
        return jsonify({'error': 'Заполните все поля'}), 400

    if not is_valid_email(email):
        return jsonify({'error': 'Неверный формат email'}), 400

    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
            (username, email, password_hash)
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        # Автоматический вход после регистрации (генерируем токен)
        token = jwt.encode({
            'user_id': user_id,
            'username': username,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }, SECRET_KEY, algorithm="HS256")

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
        if "unique" in str(e).lower():
            return jsonify({'error': 'Такой пользователь или email уже существует'}), 400
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({'error': 'Введите email и пароль'}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, username, password_hash FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
            token = jwt.encode({
                'user_id': user[0],
                'username': user[1],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
            }, SECRET_KEY, algorithm="HS256")

            return jsonify({
                'token': token,
                'user': {
                    'id': user[0],
                    'username': user[1],
                    'email': email
                }
            }), 200
        else:
            return jsonify({'error': 'Неверный email или пароль'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/me', methods=['GET'])
@token_required
def get_me():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, username, email FROM users WHERE id = %s", (request.user_id,))
        user_row = cur.fetchone()
        cur.close()
        conn.close()

        if user_row:
            return jsonify({
                'id': user_row[0],
                'username': user_row[1],
                'email': user_row[2]
            }), 200
        else:
            return jsonify({'error': 'Пользователь не найден'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
