from flask import Blueprint, request, jsonify
import sys
import os

# Добавляем родительскую директорию в path
api_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)

from db import get_db_connection
from .auth import token_required, SECRET_KEY
import jwt

words_bp = Blueprint('words', __name__, url_prefix='/api')

def get_current_user_id():
    """Безопасно получаем user_id из заголовка (опционально)"""
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(" ")[1]
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            return data['user_id']
        except:
            pass
    return None

@words_bp.route('/words', methods=['GET'])
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
        
        conn = get_db_connection()
        cur = conn.cursor()

        # Получаем общее количество слов для уровня
        cur.execute("SELECT COUNT(*) FROM words WHERE level = %s", (level,))
        total = cur.fetchone()[0]

        # Получаем слова с пагинацией
        user_id = get_current_user_id()
        if user_id:
            cur.execute("""
                SELECT w.id, w.level, w.topic, w.de, w.ru, w.article, w.verb_forms, w.example_de, w.example_ru, w.audio_url,
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

        cur.close()
        conn.close()
        
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
def get_word(word_id: int):
    """Получить одно слово по ID"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        user_id = get_current_user_id()
        if user_id:
            cur.execute("""
                SELECT w.id, w.level, w.topic, w.de, w.ru, w.article, w.verb_forms, w.example_de, w.example_ru, w.audio_url,
                       (f.word_id IS NOT NULL) as is_favorite
                FROM words w
                LEFT JOIN user_favorites f ON w.id = f.word_id AND f.user_id = %s
                WHERE w.id = %s AND (w.user_id IS NULL OR w.user_id = %s)
            """, (user_id, word_id, user_id))
        else:
            cur.execute("""
                SELECT id, level, topic, de, ru, article, verb_forms, example_de, example_ru, audio_url,
                       false as is_favorite
                FROM words 
                WHERE id = %s AND user_id IS NULL
            """, (word_id,))
        
        row = cur.fetchone()
        columns = [desc[0] for desc in cur.description]
        cur.close()
        conn.close()
        
        if not row:
            return jsonify({"error": "Слово не найдено"}), 404
        
        result = dict(zip(columns, row))
        
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@words_bp.route('/words/by-topic/<topic>', methods=['GET'])
def get_words_by_topic(topic: str):
    """Получить слова по теме"""
    try:
        skip = int(request.args.get("skip", 0))
        limit = min(int(request.args.get("limit", 100)), 500)
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Проверяем, что тема существует
        cur.execute("SELECT COUNT(*) FROM words WHERE topic = %s", (topic,))
        total = cur.fetchone()[0]
        
        if total == 0:
            return jsonify({"error": "Тема не найдена"}), 404
        
        cur.execute("""
            SELECT id, level, topic, de, ru, article, verb_forms, example_de, example_ru, audio_url
            FROM words 
            WHERE topic = %s
            ORDER BY id
            LIMIT %s OFFSET %s
        """, (topic, limit, skip))
        
        columns = [desc[0] for desc in cur.description]
        results = []
        for row in cur.fetchall():
            results.append(dict(zip(columns, row)))
        
        cur.close()
        conn.close()
        
        return jsonify({
            "data": results,
            "total": total,
            "skip": skip,
            "limit": limit
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@words_bp.route('/levels', methods=['GET'])
def get_levels():
    """Получить список всех доступных уровней"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT DISTINCT level FROM words ORDER BY level")
        levels = [row[0] for row in cur.fetchall()]
        
        cur.close()
        conn.close()
        
        return jsonify({"levels": levels}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@words_bp.route('/topics', methods=['GET'])
def get_topics():
    """Получить список всех доступных тем"""
    try:
        level = request.args.get("level")
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        if level:
            cur.execute("SELECT DISTINCT topic FROM words WHERE level = %s ORDER BY topic", (level,))
        else:
            cur.execute("SELECT DISTINCT topic FROM words ORDER BY topic")
        
        topics = [row[0] for row in cur.fetchall()]
        
        cur.close()
        conn.close()
        
        return jsonify({"topics": topics}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@words_bp.route('/words/search', methods=['GET'])
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
        
        if user_id:
            cur.execute("""
                SELECT w.id, w.level, w.topic, w.de, w.ru, w.article, w.verb_forms, w.example_de, w.example_ru, w.audio_url,
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
            
        cur.close()
        conn.close()
        
        return jsonify({"data": results, "query": query}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@words_bp.route('/favorites', methods=['GET'])
@token_required
def get_favorites():
    """Получить список избранных слов пользователя"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT w.id, w.level, w.topic, w.de, w.ru, w.article, w.verb_forms, w.example_de, w.example_ru, w.audio_url,
                   true as is_favorite
            FROM words w
            JOIN user_favorites f ON w.id = f.word_id
            WHERE f.user_id = %s
            ORDER BY f.created_at DESC
        """, (request.user_id,))
        
        columns = [desc[0] for desc in cur.description]
        results = [dict(zip(columns, row)) for row in cur.fetchall()]
        
        cur.close()
        conn.close()
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@words_bp.route('/words/<int:word_id>/favorite', methods=['POST'])
@token_required
def toggle_favorite(word_id: int):
    """Добавить или удалить слово из избранного"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Проверяем, в избранном ли оно уже
        cur.execute("SELECT 1 FROM user_favorites WHERE user_id = %s AND word_id = %s", (request.user_id, word_id))
        is_fav = cur.fetchone()
        
        if is_fav:
            cur.execute("DELETE FROM user_favorites WHERE user_id = %s AND word_id = %s", (request.user_id, word_id))
            status = "removed"
        else:
            cur.execute("INSERT INTO user_favorites (user_id, word_id) VALUES (%s, %s)", (request.user_id, word_id))
            status = "added"
            
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "success", "action": status}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@words_bp.route('/words/custom', methods=['POST'])
@token_required
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
            
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                INSERT INTO words (de, ru, article, level, topic, verb_forms, example_de, example_ru, user_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (de, ru, article, level, topic, verb_forms, example_de, example_ru, request.user_id))
            
            word_id = cur.fetchone()[0]
            conn.commit()
            
            cur.close()
            conn.close()
            return jsonify({"status": "success", "word_id": word_id}), 201
        except Exception as e:
            if "unique" in str(e).lower():
                return jsonify({"error": "Такое слово уже есть в вашем списке или в общем доступе"}), 400
            raise e
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500
