from flask import Blueprint, request, jsonify, g
from .db import get_db
from .schemas import UserSchema # Предполагаем, что схема пользователя есть в schemas.py
from datetime import datetime
import logging

# Настройка логирования
logger = logging.getLogger(__name__)

# Создаем новый Blueprint для админских маршрутов
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/users', methods=['GET'])
def get_admin_users():
    """
    Эндпоинт для получения списка пользователей для админ-панели.
    Поддерживает пагинацию, поиск и фильтрацию по статусу.
    """
    try:
        db = get_db()
        cursor = db.cursor()

        # Получаем параметры пагинации и поиска из запроса
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        search = request.args.get('search', '')
        
        # Определяем смещение для запроса к БД
        offset = (page - 1) * limit

        # Формируем базовый SQL-запрос
        query_users = """
            SELECT id, username, email, created_at, is_active
            FROM users
            WHERE 1=1
        """
        query_count = "SELECT COUNT(*) FROM users WHERE 1=1"
        params = []

        # Добавляем условия поиска, если он есть
        if search:
            search_pattern = f"%{search}%"
            query_users += " AND (username ILIKE %s OR email ILIKE %s)"
            query_count += " AND (username ILIKE %s OR email ILIKE %s)"
            params.extend([search_pattern, search_pattern])

        # Добавляем сортировку (по дате создания, например)
        query_users += " ORDER BY created_at DESC"

        # Добавляем лимит и смещение для пагинации
        query_users += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        # Выполняем запрос для получения пользователей
        cursor.execute(query_users, tuple(params))
        users_data = cursor.fetchall()

        # Выполняем запрос для получения общего количества пользователей
        cursor.execute(query_count, tuple(params[:-2] if search else params)) # Убираем limit и offset из params для count
        total_count = cursor.fetchone()[0]

        # Форматируем результат
        users_list = []
        # Предполагаем, что db.cursor() возвращает строки, которые можно перебрать
        # Если используется psycopg2, можно использовать RealDictCursor для словарей
        # Или же, если строки возвращаются как кортежи, нужно знать порядок столбцов
        # Предположим, что порядок: id, username, email, created_at, is_active
        for row in users_data:
            user_obj = {
                "id": row[0],
                "username": row[1],
                "email": row[2],
                "created_at": row[3].isoformat() if isinstance(row[3], datetime) else str(row[3]),
                "is_active": row[4] if row[4] is not None else True # По умолчанию активен, если нет данных
            }
            users_list.append(user_obj)

        # Формируем ответ
        response_data = {
            "users": users_list,
            "total": total_count,
            "page": page,
            "limit": limit,
        }
        
        return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"Error fetching admin users: {e}", exc_info=True)
        return jsonify({"error": "Ошибка при загрузке пользователей", "details": str(e)}), 500
    finally:
        if 'db' in locals() and db:
            db.close()

# Можно добавить другие эндпоинты для админки здесь (например, для обновления, удаления пользователей)
