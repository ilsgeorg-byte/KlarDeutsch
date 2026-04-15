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
    db = None # Инициализируем db вне try, чтобы использовать в finally
    try:
        db = get_db()
        # Предполагаем, что get_db() возвращает соединение psycopg2,
        # которое при использовании cursor() возвращает строки как кортежи.
        # Если используется RealDictCursor, доступ будет по именам ключей.
        cursor = db.cursor() 

        # Получаем параметры пагинации и поиска из запроса
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        search = request.args.get('search', '')
        
        # Определяем смещение для запроса к БД
        offset = (page - 1) * limit

        # Формируем базовый SQL-запрос
        query_users_sql = """
            SELECT id, username, email, created_at, is_active
            FROM users
            WHERE 1=1
        """
        query_count_sql = "SELECT COUNT(*) FROM users WHERE 1=1"
        params = []

        # Добавляем условия поиска, если он есть
        if search:
            search_pattern = f"%{search}%"
            # Используем ILIKE для регистронезависимого поиска
            query_users_sql += " AND (username ILIKE %s OR email ILIKE %s)"
            query_count_sql += " AND (username ILIKE %s OR email ILIKE %s)"
            params.extend([search_pattern, search_pattern])

        # Добавляем сортировку (по дате создания, например)
        query_users_sql += " ORDER BY created_at DESC"

        # Добавляем лимит и смещение для пагинации
        query_users_sql += " LIMIT %s OFFSET %s"
        params_for_users = params + [limit, offset] # Создаем копию для запроса пользователей

        # Логируем SQL-запрос и параметры перед выполнением
        logger.info(f"Executing SQL query for users: {query_users_sql}")
        logger.info(f"With parameters: {params_for_users}")

        # Выполняем запрос для получения пользователей
        cursor.execute(query_users_sql, tuple(params_for_users))
        users_data = cursor.fetchall()

        # Логируем сырые данные, полученные из БД
        logger.info(f"Raw users data fetched from DB: {users_data}")

        # Выполняем запрос для получения общего количества пользователей
        # Убираем limit и offset из params для count, если они были добавлены
        params_for_count = params if search else []
        logger.info(f"Executing SQL query for count: {query_count_sql}")
        logger.info(f"With parameters for count: {params_for_count}")
        cursor.execute(query_count_sql, tuple(params_for_count))
        total_count = cursor.fetchone()[0]

        # Форматируем результат
        users_list = []
        # Обработка строк, полученных из fetchall()
        # Предполагаемый порядок столбцов: id, username, email, created_at, is_active
        for row in users_data:
            # Проверяем, что строка имеет ожидаемое количество столбцов
            if len(row) < 5:
                logger.error(f"Unexpected row structure from DB: {row}. Expected at least 5 columns.")
                continue # Пропускаем некорректную строку

            user_id, username, email, created_at_raw, is_active_raw = row[0], row[1], row[2], row[3], row[4]
            
            # Безопасное преобразование created_at
            created_at_str = ""
            if isinstance(created_at_raw, datetime):
                created_at_str = created_at_raw.isoformat()
            elif isinstance(created_at_raw, str):
                created_at_str = created_at_raw # Уже строка
            else:
                logger.warning(f"Unexpected type for created_at: {type(created_at_raw)}. Value: {created_at_raw}. Converting to string.")
                created_at_str = str(created_at_raw)

            # Безопасное преобразование is_active
            # Предполагаем, что в БД может быть NULL, False, True, 0, 1
            is_active_bool = True # По умолчанию True, если значение отсутствует или не распознано
            if is_active_raw is False or is_active_raw == 0:
                is_active_bool = False
            elif is_active_raw is True or is_active_raw == 1:
                is_active_bool = True
            elif is_active_raw is None:
                is_active_bool = True # Как указано в изначальном коде, None -> True
            else:
                logger.warning(f"Unexpected type or value for is_active: {type(is_active_raw)}, {is_active_raw}. Defaulting to True.")
                is_active_bool = True

            user_obj = {
                "id": user_id,
                "username": username,
                "email": email,
                "created_at": created_at_str,
                "is_active": is_active_bool
            }
            users_list.append(user_obj)

        # Формируем ответ
        response_data = {
            "users": users_list,
            "total": total_count,
            "page": page,
            "limit": limit,
        }
        
        logger.info(f"Successfully fetched {len(users_list)} users. Total: {total_count}")
        return jsonify(response_data), 200

    except Exception as e:
        # Логируем ошибку с подробностями
        logger.error(f"Error fetching admin users: {e}", exc_info=True)
        # Возвращаем 500 ошибку с деталями, если это не проблема авторизации/валидации
        return jsonify({"error": "Ошибка при загрузке пользователей", "details": str(e)}), 500
    finally:
        # Закрываем соединение с БД
        if db:
            db.close()
            logger.info("Database connection closed.")

# Можно добавить другие эндпоинты для админки здесь (например, для обновления, удаления пользователей)
