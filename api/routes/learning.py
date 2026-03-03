from flask import Blueprint, request, jsonify
import os
import sys
import logging

api_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)

from .auth import token_required
from db import get_db_connection

learning_bp = Blueprint('learning', __name__, url_prefix='/api/learning')
logger = logging.getLogger(__name__)


@learning_bp.route('/words', methods=['GET'])
@token_required
def get_learning_words():
    """
    Получить ВСЕ слова в изучении (статус 'learning')
    Query параметры:
    - level: A1, A2, B1, B2, C1 (опционально, фильтр по уровню)
    """
    try:
        level = request.args.get("level")
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        if level:
            # Слова конкретного уровня в изучении
            cur.execute("""
                SELECT w.id, w.level, w.topic, w.de, w.ru, w.article, w.verb_forms, 
                       w.example_de, w.example_ru, w.audio_url,
                       uw.interval, uw.ease_factor, uw.reps, uw.next_review
                FROM words w
                JOIN user_words uw ON w.id = uw.word_id
                WHERE w.level = %s AND uw.user_id = %s AND uw.status = 'learning'
                ORDER BY uw.next_review ASC
            """, (level, request.user_id))
        else:
            # Все слова в изучении
            cur.execute("""
                SELECT w.id, w.level, w.topic, w.de, w.ru, w.article, w.verb_forms, 
                       w.example_de, w.example_ru, w.audio_url,
                       uw.interval, uw.ease_factor, uw.reps, uw.next_review
                FROM words w
                JOIN user_words uw ON w.id = uw.word_id
                WHERE uw.user_id = %s AND uw.status = 'learning'
                ORDER BY w.level, uw.next_review ASC
            """, (request.user_id,))
        
        columns = [desc[0] for desc in cur.description]
        words = [dict(zip(columns, row)) for row in cur.fetchall()]
        
        cur.close()
        conn.close()
        
        return jsonify(words), 200
        
    except Exception as e:
        logger.error(f"Error getting learning words: {e}")
        return jsonify({"error": str(e)}), 500


@learning_bp.route('/stats', methods=['GET'])
@token_required
def get_learning_stats():
    """
    Получить детальную статистику по изучению
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Статистика по уровням
        cur.execute("""
            SELECT w.level, uw.status, COUNT(*) as count
            FROM user_words uw
            JOIN words w ON uw.word_id = w.id
            WHERE uw.user_id = %s
            GROUP BY w.level, uw.status
            ORDER BY w.level
        """, (request.user_id,))
        
        stats = []
        for row in cur.fetchall():
            stats.append({
                "level": row[0],
                "status": row[1],
                "count": row[2]
            })
        
        cur.close()
        conn.close()
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
