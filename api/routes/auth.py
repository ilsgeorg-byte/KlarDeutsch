import jwt
import datetime
import bcrypt
from flask import Blueprint, request, jsonify, current_app
from functools import wraps
from api.db import get_db_connection

auth_bp = Blueprint('auth', __name__)

# Секретный ключ (в продакшене должен быть в .env.local)
SECRET_KEY = "klardeutsch-super-secret-key"

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({'error': 'Токен отсутствует'}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            # Прикрепляем user_id к запросу
            request.user_id = data['user_id']
        except Exception as e:
            return jsonify({'error': 'Неверный токен'}), 401

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

        return jsonify({'status': 'success', 'message': 'Пользователь зарегистрирован'}), 201
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
