from flask import Blueprint, request, jsonify
import sys
import os

# Добавляем родительскую директорию в path
api_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)

from db import get_db_connection

words_bp = Blueprint('words', __name__, url_prefix='/api')

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
        
        print(f"📝 Запрос слов: level={level}, skip={skip}, limit={limit}")
        
        # Валидация уровня
        allowed_levels = ["A1", "A2", "B1", "B2", "C1"]
        if level not in allowed_levels:
            return jsonify({"error": f"Неверный уровень. Допустимые: {', '.join(allowed_levels)}"}), 400
        
        print(f"🔗 Подключение к БД...")
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Получаем общее количество слов для уровня
        print(f"📊 Подсчет слов для уровня {level}...")
        cur.execute("SELECT COUNT(*) FROM words WHERE level = %s", (level,))
        total = cur.fetchone()[0]
        print(f"✅ Найдено слов: {total}")
        
        # Получаем слова с пагинацией
        print(f"📥 Получение слов с LIMIT {limit} OFFSET {skip}...")
        cur.execute("""
            SELECT id, level, topic, de, ru, article, example_de, example_ru, audio_url
            FROM words 
            WHERE level = %s
            ORDER BY id
            LIMIT %s OFFSET %s
        """, (level, limit, skip))
        
        columns = [desc[0] for desc in cur.description]
        results = []
        for row in cur.fetchall():
            results.append(dict(zip(columns, row)))
        
        print(f"✅ Возвращаем {len(results)} слов")
        
        cur.close()
        conn.close()
        
        return jsonify({
            "data": results,
            "total": total,
            "skip": skip,
            "limit": limit
        }), 200
    
    except ValueError as e:
        print(f"❌ ValueError: {str(e)}")
        return jsonify({"error": f"Неверные параметры: {str(e)}"}), 400
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "type": type(e).__name__}), 500

@words_bp.route('/words/<int:word_id>', methods=['GET'])
def get_word(word_id: int):
    """Получить одно слово по ID"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, level, topic, de, ru, article, example_de, example_ru, audio_url
            FROM words 
            WHERE id = %s
        """, (word_id,))
        
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if not row:
            return jsonify({"error": "Слово не найдено"}), 404
        
        columns = ['id', 'level', 'topic', 'de', 'ru', 'article', 'example_de', 'example_ru', 'audio_url']
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
            SELECT id, level, topic, de, ru, article, example_de, example_ru, audio_url
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
