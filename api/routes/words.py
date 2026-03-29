from flask import Blueprint, request, jsonify
import sys
import os
import logging
import json
import csv
import io

# Добавляем родительскую директорию в path 1
api_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)

from db import get_db_connection, get_db_cursor
from .auth import token_required, SECRET_KEY
from utils.token_utils import get_current_user_id_optional
from utils.cache_decorator import cache_response, cache_invalidate, invalidate_user_cache

words_bp = Blueprint('words', __name__, url_prefix='/api')

# Логгер
logger = logging.getLogger(__name__)

def get_current_user_id():
    """
    Безопасно получаем user_id из заголовка (опционально)
    
    Используется для персонализации ответов (избранные слова и т.п.)
    При ошибке токена возвращает None и логирует событие.
    
    Returns:
        user_id если токен валиден, иначе None
    """
    user_id = get_current_user_id_optional()
    if user_id is None:
        # Проверяем, есть ли вообще заголовок Authorization
        auth_header = request.headers.get('Authorization')
        if auth_header:
            logger.debug("Запрос с авторизацией, но токен не валиден (возможно, истёк или не принадлежит пользователю)")
    return user_id

@words_bp.route('/words', methods=['GET'])
@cache_response('words:list', ttl=3600)
def get_words():
    """
    Получить список слов по уровню.
    Query параметры:
    - level: A1, A2, B1, B2, C1 (по умолчанию A1)
    - skip: количество пропускаемых записей (для пагинации)
    - limit: максимум записей (по умолчанию 100)
    """
    try:
        level = request.args.get("level", "A1").upper()
        skip = int(request.args.get("skip", 0))
        limit = min(int(request.args.get("limit", 100)), 500)  # Максимум 500
        
        # Валидация уровня
        allowed_levels = ["A1", "A2", "B1", "B2", "C1"]
        if level not in allowed_levels:
            return jsonify({"error": f"Неверный уровень. Допустимые: {', '.join(allowed_levels)}"}), 400
        
        with get_db_cursor() as cur:
            # Получаем общее количество слов для уровня
            cur.execute("SELECT COUNT(*) FROM words WHERE level = %s", (level,))
            total = cur.fetchone()[0]

            # Получаем слова с пагинацией И НОВЫМИ КОЛОНКАМИ
            user_id = get_current_user_id()
            if user_id:
                cur.execute("""
                    SELECT w.id, w.level, w.topic, w.de, w.ru, w.article, w.verb_forms, w.example_de, w.example_ru, w.audio_url,
                           w.plural, w.examples, w.synonyms, w.antonyms, w.collocations,
                           (f.word_id IS NOT NULL) as is_favorite
                    FROM words w
                    LEFT JOIN user_favorites f ON w.id = f.word_id AND f.user_id = %s
                    WHERE w.level = %s AND (w.user_id IS NULL OR w.user_id = %s)
                    ORDER BY w.id
                    LIMIT %s OFFSET %s
                """, (user_id, level, user_id, limit, skip))
            else:
                cur.execute("""
                    SELECT id, level, topic, de, ru, article, verb_forms, example_de, example_ru, audio_url,
                           plural, examples, synonyms, antonyms, collocations,
                           false as is_favorite
                    FROM words
                    WHERE level = %s AND user_id IS NULL
                    ORDER BY id
                    LIMIT %s OFFSET %s
                """, (level, limit, skip))

            columns = [desc[0] for desc in cur.description]
            results = []
            for row in cur.fetchall():
                results.append(dict(zip(columns, row)))
        
        return jsonify({
            "data": results,
            "total": total,
            "skip": skip,
            "limit": limit
        }), 200
    
    except ValueError as e:
        return jsonify({"error": f"Неверные параметры: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": str(e), "type": type(e).__name__}), 500

@words_bp.route('/words/<int:word_id>', methods=['GET'])
@cache_response('words:detail', ttl=3600)
def get_word(word_id: int):
    """Получить одно слово по ID"""
    try:
        with get_db_cursor() as cur:
            user_id = get_current_user_id()
            if user_id:
                cur.execute("""
                    SELECT w.id, w.level, w.topic, w.de, w.ru, w.article, w.verb_forms, w.example_de, w.example_ru, w.audio_url,
                           w.plural, w.examples, w.synonyms, w.antonyms, w.collocations,
                           (f.word_id IS NOT NULL) as is_favorite
                    FROM words w
                    LEFT JOIN user_favorites f ON w.id = f.word_id AND f.user_id = %s
                    WHERE w.id = %s AND (w.user_id IS NULL OR w.user_id = %s)
                """, (user_id, word_id, user_id))
            else:
                cur.execute("""
                    SELECT id, level, topic, de, ru, article, verb_forms, example_de, example_ru, audio_url,
                           plural, examples, synonyms, antonyms, collocations,
                           false as is_favorite
                    FROM words
                    WHERE id = %s AND user_id IS NULL
                """, (word_id,))
            
            row = cur.fetchone()
            columns = [desc[0] for desc in cur.description]
            
            if not row:
                return jsonify({"error": "Слово не найдено"}), 404
            
            result = dict(zip(columns, row))
            
            return jsonify(result), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@words_bp.route('/words/by-topic/<topic>', methods=['GET'])
@cache_response('words:topic', ttl=3600)
def get_words_by_topic(topic: str):
    """Получить слова по теме"""
    try:
        skip = int(request.args.get("skip", 0))
        limit = min(int(request.args.get("limit", 100)), 500)
        
        with get_db_cursor() as cur:
            # Проверяем, что тема существует
            cur.execute("SELECT COUNT(*) FROM words WHERE topic = %s", (topic,))
            total = cur.fetchone()[0]
            
            if total == 0:
                return jsonify({"error": "Тема не найдена"}), 404
            
            cur.execute("""
                SELECT id, level, topic, de, ru, article, verb_forms, example_de, example_ru, audio_url,
                       plural, examples, synonyms, antonyms, collocations
                FROM words
                WHERE topic = %s
                ORDER BY id
                LIMIT %s OFFSET %s
            """, (topic, limit, skip))
            
            columns = [desc[0] for desc in cur.description]
            results = []
            for row in cur.fetchall():
                results.append(dict(zip(columns, row)))
            
            return jsonify({
                "data": results,
                "total": total,
                "skip": skip,
                "limit": limit
            }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@words_bp.route('/levels', methods=['GET'])
@cache_response('words:levels', ttl=86400)
def get_levels():
    """Получить список всех доступных уровней"""
    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT DISTINCT level FROM words ORDER BY level")
            levels = [row[0] for row in cur.fetchall()]
            
            return jsonify({"levels": levels}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@words_bp.route('/topics', methods=['GET'])
@cache_response('words:topics', ttl=86400)
def get_topics():
    """Получить список всех доступных тем"""
    try:
        level = request.args.get("level")
        
        with get_db_cursor() as cur:
            if level:
                cur.execute("SELECT DISTINCT topic FROM words WHERE level = %s ORDER BY topic", (level,))
            else:
                cur.execute("SELECT DISTINCT topic FROM words ORDER BY topic")
            
            topics = [row[0] for row in cur.fetchall()]
            
            return jsonify({"topics": topics}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@words_bp.route('/words/search', methods=['GET'])
@cache_response('words:search', ttl=300)
def search_words():
    """
    Поиск слов по тексту (немецкий или русский).
    Query параметры:
    - q: поисковый запрос (минимум 2 символа)
    - limit: максимум результатов (по умолчанию 50)
    """
    try:
        query = request.args.get("q", "").strip()
        limit = min(int(request.args.get("limit", 50)), 100)
        
        search_pattern = f"%{query}%"
        
        if len(query) < 2:
            return jsonify({"data": [], "message": "Запрос слишком короткий (мин. 2 символа)"}), 200
            
        user_id = get_current_user_id()
        
        with get_db_cursor() as cur:
            if user_id:
                cur.execute("""
                    SELECT w.id, w.level, w.topic, w.de, w.ru, w.article, w.verb_forms, w.example_de, w.example_ru, w.audio_url,
                           w.plural, w.examples, w.synonyms, w.antonyms, w.collocations,
                           (f.word_id IS NOT NULL) as is_favorite
                    FROM words w
                    LEFT JOIN user_favorites f ON w.id = f.word_id AND f.user_id = %s
                    WHERE (w.de ILIKE %s OR w.ru ILIKE %s) AND (w.user_id IS NULL OR w.user_id = %s)
                    ORDER BY
                        CASE
                            WHEN w.de ILIKE %s THEN 1
                            WHEN w.ru ILIKE %s THEN 2
                            ELSE 3
                        END,
                        w.de
                    LIMIT %s
                """, (user_id, search_pattern, search_pattern, user_id, query, query, limit))
            else:
                cur.execute("""
                    SELECT id, level, topic, de, ru, article, verb_forms, example_de, example_ru, audio_url,
                           plural, examples, synonyms, antonyms, collocations,
                           false as is_favorite
                    FROM words
                    WHERE (de ILIKE %s OR ru ILIKE %s) AND user_id IS NULL
                    ORDER BY
                        CASE
                            WHEN de ILIKE %s THEN 1
                            WHEN ru ILIKE %s THEN 2
                            ELSE 3
                        END,
                        de
                    LIMIT %s
                """, (search_pattern, search_pattern, query, query, limit))
            
            columns = [desc[0] for desc in cur.description]
            results = []
            for row in cur.fetchall():
                results.append(dict(zip(columns, row)))
                
            return jsonify({"data": results, "query": query}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@words_bp.route('/favorites', methods=['GET'])
@token_required
@cache_response('user:favorites', ttl=300, user_specific=True)
def get_favorites():
    """Получить список избранных слов пользователя"""
    try:
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT w.id, w.level, w.topic, w.de, w.ru, w.article, w.verb_forms, w.example_de, w.example_ru, w.audio_url,
                       w.plural, w.examples, w.synonyms, w.antonyms, w.collocations,
                       true as is_favorite
                FROM words w
                JOIN user_favorites f ON w.id = f.word_id
                WHERE f.user_id = %s
                ORDER BY f.created_at DESC
            """, (request.user_id,))
            
            columns = [desc[0] for desc in cur.description]
            results = [dict(zip(columns, row)) for row in cur.fetchall()]
            
            return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@words_bp.route('/words/<int:word_id>/favorite', methods=['POST'])
@token_required
@cache_invalidate('user:favorites:*')
def toggle_favorite(word_id: int):
    """Добавить или удалить слово из избранного"""
    try:
        with get_db_cursor() as cur:
            # Проверяем, в избранном ли оно уже
            cur.execute("SELECT 1 FROM user_favorites WHERE user_id = %s AND word_id = %s", (request.user_id, word_id))
            is_fav = cur.fetchone()

            if is_fav:
                cur.execute("DELETE FROM user_favorites WHERE user_id = %s AND word_id = %s", (request.user_id, word_id))
                status = "removed"
            else:
                cur.execute("INSERT INTO user_favorites (user_id, word_id) VALUES (%s, %s)", (request.user_id, word_id))
                status = "added"

            # Инвалидируем пользовательский кэш
            invalidate_user_cache(request.user_id)
            
            return jsonify({"status": "success", "action": status}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@words_bp.route('/words/<int:word_id>', methods=['PUT'])
@token_required
@cache_invalidate('words:list:*', 'words:detail:*', 'words:topics:*', 'words:search:*')
def update_word(word_id: int):
    """Обновить слово по ID (для обычных пользователей - только свои слова)"""
    try:
        data = request.json
        de = data.get('de', '').strip()
        ru = data.get('ru', '').strip()
        article = data.get('article', '').strip()
        level = data.get('level', 'A1')
        topic = data.get('topic', '').strip()
        verb_forms = data.get('verb_forms', '').strip()
        example_de = data.get('example_de', '').strip()
        example_ru = data.get('example_ru', '').strip()

        if not de or not ru:
            return jsonify({"error": "Поля 'de' и 'ru' обязательны"}), 400

        with get_db_cursor() as cur:
            # Проверяем, существует ли слово и принадлежит ли оно пользователю
            cur.execute("SELECT user_id FROM words WHERE id = %s", (word_id,))
            result = cur.fetchone()
            
            if not result:
                return jsonify({"error": "Слово не найдено"}), 404
            
            word_user_id = result[0]
            # Только администраторы могут изменять общие слова (где user_id IS NULL)
            # Пользователи могут изменять только свои слова
            if word_user_id is not None and word_user_id != request.user_id:
                return jsonify({"error": "Нет прав для изменения этого слова"}), 403

            # Обновляем слово
            cur.execute("""
                UPDATE words
                SET de = %s, ru = %s, article = %s, level = %s, topic = %s,
                    verb_forms = %s, plural = %s, example_de = %s, example_ru = %s,
                    synonyms = %s, antonyms = %s, collocations = %s, examples = %s
                WHERE id = %s
            """, (
                de, ru, article, level, topic, 
                verb_forms, data.get('plural', '').strip(),
                example_de, example_ru,
                data.get('synonyms', '').strip(),
                data.get('antonyms', '').strip(),
                data.get('collocations', '').strip(),
                json.dumps(data.get('examples', [])),
                word_id
            ))

            if cur.rowcount == 0:
                return jsonify({"error": "Слово не найдено"}), 404

            # Инвалидируем пользовательский кэш
            invalidate_user_cache(request.user_id)
            
            return jsonify({"status": "success", "word_id": word_id}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@words_bp.route('/admin/words/<int:word_id>', methods=['PUT'])
@token_required
def update_word_admin(word_id: int):
    """Обновить слово по ID (для администраторов - любые слова)"""
    try:
        # Проверяем права администратора
        with get_db_cursor() as cur:
            cur.execute("SELECT role FROM users WHERE id = %s", (request.user_id,))
            result = cur.fetchone()
            
            if not result or result[0] != 'admin':
                return jsonify({"error": "Требуются права администратора"}), 403

        data = request.json
        de = data.get('de', '').strip()
        ru = data.get('ru', '').strip()
        article = data.get('article', '').strip()
        level = data.get('level', 'A1')
        topic = data.get('topic', '').strip()
        verb_forms = data.get('verb_forms', '').strip()
        example_de = data.get('example_de', '').strip()
        example_ru = data.get('example_ru', '').strip()

        if not de or not ru:
            return jsonify({"error": "Поля 'de' и 'ru' обязательны"}), 400

        with get_db_cursor() as cur:
            # Обновляем слово (администратор может обновить любое слово)
            cur.execute("""
                UPDATE words
                SET de = %s, ru = %s, article = %s, level = %s, topic = %s,
                    verb_forms = %s, plural = %s, example_de = %s, example_ru = %s,
                    synonyms = %s, antonyms = %s, collocations = %s, examples = %s
                WHERE id = %s
            """, (
                de, ru, article, level, topic, 
                verb_forms, data.get('plural', '').strip(),
                example_de, example_ru,
                data.get('synonyms', '').strip(),
                data.get('antonyms', '').strip(),
                data.get('collocations', '').strip(),
                json.dumps(data.get('examples', [])),
                word_id
            ))

            if cur.rowcount == 0:
                return jsonify({"error": "Слово не найдено"}), 404

            # Инвалидируем пользовательский кэш
            invalidate_user_cache(request.user_id)
            
            return jsonify({"status": "success", "word_id": word_id}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@words_bp.route('/words/custom', methods=['POST'])
@token_required
@cache_invalidate('words:list:*', 'words:topics:*', 'words:search:*')
def add_custom_word():
    """Добавить личное слово пользователя"""
    try:
        data = request.json
        de = data.get('de', '').strip()
        ru = data.get('ru', '').strip()
        article = data.get('article', '').strip()
        level = data.get('level', 'A1')
        topic = data.get('topic', 'Личные слова')
        verb_forms = data.get('verb_forms', '').strip()
        example_de = data.get('example_de', '').strip()
        example_ru = data.get('example_ru', '').strip()

        if not de or not ru:
            return jsonify({"error": "Поля 'de' и 'ru' обязательны"}), 400

        with get_db_cursor() as cur:
            try:
                cur.execute("""
                    INSERT INTO words (
                        de, ru, article, level, topic, 
                        verb_forms, plural, example_de, example_ru, 
                        synonyms, antonyms, collocations, examples, user_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    de, ru, article, level, topic, 
                    verb_forms, data.get('plural', '').strip(),
                    example_de, example_ru,
                    data.get('synonyms', '').strip(),
                    data.get('antonyms', '').strip(),
                    data.get('collocations', '').strip(),
                    json.dumps(data.get('examples', [])),
                    request.user_id
                ))

                word_id = cur.fetchone()[0]
                
                # Инвалидируем пользовательский кэш
                invalidate_user_cache(request.user_id)
                
                return jsonify({"status": "success", "word_id": word_id}), 201
            except Exception as e:
                if "unique" in str(e).lower():
                    return jsonify({"error": "Такое слово уже есть в вашем списке или в общем доступе"}), 400
                raise e

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@words_bp.route('/words/bulk-upload', methods=['POST'])
@token_required
@cache_invalidate('words:list:*', 'words:topics:*', 'words:search:*')
def bulk_upload_words():
    """Массовая загрузка слов из JSON или CSV"""
    try:
        user_id = request.user_id
        data = None
        
        # Определяем формат данных
        if request.is_json:
            data = request.get_json()
            words_list = data.get('words', [])
        elif request.files.get('file'):
            file = request.files['file']
            filename = file.filename.lower()
            
            if filename.endswith('.json'):
                content = file.read().decode('utf-8')
                json_data = json.loads(content)
                words_list = json_data.get('words', []) if isinstance(json_data, dict) else json_data
            elif filename.endswith('.csv'):
                content = file.read().decode('utf-8')
                csv_file = io.StringIO(content)
                reader = csv.DictReader(csv_file)
                words_list = list(reader)
            else:
                return jsonify({"error": "Неподдерживаемый формат файла. Используйте JSON или CSV"}), 400
        else:
            return jsonify({"error": "Нет данных для загрузки"}), 400
        
        if not isinstance(words_list, list) or len(words_list) == 0:
            return jsonify({"error": "Список слов пуст или имеет неверный формат"}), 400
        
        # Ограничиваем количество слов за раз
        if len(words_list) > 500:
            return jsonify({"error": "Максимум 500 слов за одну загрузку"}), 400
        
        added_count = 0
        skipped_count = 0
        errors = []
        
        with get_db_cursor() as cur:
            for idx, word_data in enumerate(words_list):
                try:
                    # Нормализуем ключи (поддержка разных форматов)
                    if isinstance(word_data, dict):
                        # Поддержка разных вариантов ключей
                        de = word_data.get('de') or word_data.get('german') or word_data.get('word') or ''
                        ru = word_data.get('ru') or word_data.get('russian') or word_data.get('translation') or ''
                        article = word_data.get('article') or ''
                        level = word_data.get('level') or 'A1'
                        topic = word_data.get('topic') or 'Импорт'
                        verb_forms = word_data.get('verb_forms') or word_data.get('forms') or ''
                        example_de = word_data.get('example_de') or word_data.get('example') or ''
                        example_ru = word_data.get('example_ru') or word_data.get('example_translation') or ''
                        
                        # Дополнительные поля
                        plural = word_data.get('plural') or ''
                        synonyms = word_data.get('synonyms') or ''
                        antonyms = word_data.get('antonyms') or ''
                        collocations = word_data.get('collocations') or ''
                        examples_json = word_data.get('examples') or []
                        
                        # Очищаем значения
                        de = str(de).strip()
                        ru = str(ru).strip()
                        article = str(article).strip()
                        level = str(level).strip().upper()
                        topic = str(topic).strip()
                        verb_forms = str(verb_forms).strip()
                        example_de = str(example_de).strip()
                        example_ru = str(example_ru).strip()
                        plural = str(plural).strip()
                        synonyms = str(synonyms).strip()
                        antonyms = str(antonyms).strip()
                        collocations = str(collocations).strip()
                        
                        # Валидация обязательных полей
                        if not de or not ru:
                            skipped_count += 1
                            errors.append(f"Слово #{idx + 1}: пропущено (нет de или ru)")
                            continue
                        
                        # Валидация уровня
                        if level not in ['A1', 'A2', 'B1', 'B2', 'C1']:
                            level = 'A1'
                        
                        try:
                            cur.execute("""
                                INSERT INTO words (
                                    de, ru, article, level, topic, 
                                    verb_forms, plural, example_de, example_ru, 
                                    synonyms, antonyms, collocations, examples, user_id
                                )
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT DO NOTHING
                                RETURNING id
                            """, (
                                de, ru, article, level, topic, 
                                verb_forms, plural, example_de, example_ru,
                                synonyms, antonyms, collocations, 
                                json.dumps(examples_json),
                                user_id
                            ))
                            
                            if cur.fetchone():
                                added_count += 1
                            else:
                                skipped_count += 1
                                errors.append(f"Слово #{idx + 1}: уже существует")
                        except Exception as insert_error:
                            if "unique" in str(insert_error).lower():
                                skipped_count += 1
                                errors.append(f"Слово #{idx + 1}: уже существует")
                            else:
                                raise insert_error
                    else:
                        skipped_count += 1
                        errors.append(f"Слово #{idx + 1}: неверный формат записи")
                
                except Exception as word_error:
                    skipped_count += 1
                    errors.append(f"Слово #{idx + 1}: ошибка - {str(word_error)}")
        
        # Инвалидируем пользовательский кэш
        invalidate_user_cache(user_id)
        
        response = {
            "status": "success",
            "added": added_count,
            "skipped": skipped_count,
            "total": len(words_list)
        }
        
        if errors and len(errors) <= 10:
            response["errors"] = errors
        elif errors:
            response["errors"] = errors[:10] + [f"... и ещё {len(errors) - 10} ошибок"]
        
        return jsonify(response), 201
        
    except json.JSONDecodeError:
        return jsonify({"error": "Неверный формат JSON"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@words_bp.route('/words/my-words', methods=['GET'])
@token_required
@cache_response('user:my_words', ttl=300, user_specific=True)
def get_my_words():
    """Получить список личных слов пользователя"""
    try:
        user_id = request.user_id
        skip = int(request.args.get("skip", 0))
        limit = min(int(request.args.get("limit", 100)), 500)
        level = request.args.get("level", "").upper()
        
        with get_db_cursor() as cur:
            # Общее количество
            if level:
                cur.execute("SELECT COUNT(*) FROM words WHERE user_id = %s AND level = %s", (user_id, level))
            else:
                cur.execute("SELECT COUNT(*) FROM words WHERE user_id = %s", (user_id,))
            
            total = cur.fetchone()[0]
            
            # Получаем слова
            if level:
                cur.execute("""
                    SELECT id, level, topic, de, ru, article, verb_forms, example_de, example_ru, audio_url,
                           plural, examples, synonyms, antonyms, collocations,
                           true as is_favorite
                    FROM words
                    WHERE user_id = %s AND level = %s
                    ORDER BY id DESC
                    LIMIT %s OFFSET %s
                """, (user_id, level, limit, skip))
            else:
                cur.execute("""
                    SELECT id, level, topic, de, ru, article, verb_forms, example_de, example_ru, audio_url,
                           plural, examples, synonyms, antonyms, collocations,
                           true as is_favorite
                    FROM words
                    WHERE user_id = %s
                    ORDER BY id DESC
                    LIMIT %s OFFSET %s
                """, (user_id, limit, skip))
            
            columns = [desc[0] for desc in cur.description]
            results = []
            for row in cur.fetchall():
                results.append(dict(zip(columns, row)))
            
            return jsonify({
                "data": results,
                "total": total,
                "skip": skip,
                "limit": limit
            }), 200
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@words_bp.route('/words/my-words/<int:word_id>', methods=['DELETE'])
@token_required
@cache_invalidate('user:my_words:*')
def delete_my_word(word_id: int):
    """Удалить личное слово пользователя"""
    try:
        user_id = request.user_id
        
        with get_db_cursor() as cur:
            # Проверяем, что слово принадлежит пользователю
            cur.execute("SELECT user_id FROM words WHERE id = %s", (word_id,))
            result = cur.fetchone()
            
            if not result:
                return jsonify({"error": "Слово не найдено"}), 404
            
            if result[0] != user_id:
                return jsonify({"error": "Нет прав для удаления этого слова"}), 403
            
            # Удаляем слово
            cur.execute("DELETE FROM words WHERE id = %s AND user_id = %s", (word_id, user_id))
            
            # Инвалидируем пользовательский кэш
            invalidate_user_cache(user_id)
            
            return jsonify({"status": "success", "word_id": word_id}), 200
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500
