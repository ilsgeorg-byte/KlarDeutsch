from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import os
import sys

# Добавляем родительскую директорию в path
api_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)

from .auth import token_required
from db import get_db_connection

trainer_bp = Blueprint('trainer', __name__, url_prefix='/api/trainer')

@trainer_bp.route('/words', methods=['GET'])
@token_required
def get_training_words():
    """
    Получить слова для тренировки:
    1. Слова, которые пора повторить (next_review <= now)
    2. Новые слова из выбранного уровня (которых еще нет в user_words)
    """
    try:
        level = request.args.get("level", "A1").upper()
        limit = int(request.args.get("limit", 10))
        
        # Определяем список уровней для выборки (кумулятивно)
        all_levels = ["A1", "A2", "B1", "B2", "C1"]
        if level in all_levels:
            target_levels = all_levels[:all_levels.index(level) + 1]
        else:
            target_levels = [level]
            
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. Получаем слова, которые пора повторить
        cur.execute("""
            SELECT w.id, w.level, w.topic, w.de, w.ru, w.article, w.example_de, w.example_ru, 
                   uw.interval, uw.ease_factor, uw.reps, uw.next_review
            FROM words w
            JOIN user_words uw ON w.id = uw.word_id
            WHERE w.level IN %s AND uw.user_id = %s AND uw.next_review <= CURRENT_TIMESTAMP AND uw.status = 'learning'
            ORDER BY uw.next_review ASC
            LIMIT %s
        """, (tuple(target_levels), request.user_id, limit))
        
        columns = [desc[0] for desc in cur.description]
        cards_to_review = [dict(zip(columns, row)) for row in cur.fetchall()]
        
        # 2. Если слов меньше лимита, добавляем новые
        remaining = limit - len(cards_to_review)
        if remaining > 0:
            cur.execute("""
                SELECT id, level, topic, de, ru, article, example_de, example_ru
                FROM words
                WHERE level IN %s AND id NOT IN (SELECT word_id FROM user_words WHERE user_id = %s)
                ORDER BY id
                LIMIT %s
            """, (tuple(target_levels), request.user_id, remaining))
            
            columns = [desc[0] for desc in cur.description]
            new_words = [dict(zip(columns, row)) for row in cur.fetchall()]
            cards_to_review.extend(new_words)
            
        cur.close()
        conn.close()
        
        return jsonify(cards_to_review), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@trainer_bp.route('/rate', methods=['POST'])
@token_required
def rate_word():
    """
    Обновить прогресс слова по алгоритму SM-2
    Rating: 0 (Знаю - пропускать), 1 (Сложно), 3 (Хорошо), 5 (Легко)
    """
    try:
        data = request.json
        word_id = data.get('word_id')
        rating = int(data.get('rating', -1))
        
        if not word_id or rating not in [0, 1, 3, 5]:
            return jsonify({"error": "Неверные данные"}), 400
            
        conn = get_db_connection()
        cur = conn.cursor()
        
        if rating == 0:
            # Пометить как "известное" навсегда
            cur.execute("""
                INSERT INTO user_words (user_id, word_id, status, next_review)
                VALUES (%s, %s, 'known', '2099-01-01')
                ON CONFLICT (user_id, word_id) DO UPDATE SET status = 'known', next_review = '2099-01-01'
            """, (request.user_id, word_id))
        else:
            # Получаем текущий прогресс
            cur.execute("SELECT interval, ease_factor, reps FROM user_words WHERE word_id = %s AND user_id = %s", (word_id, request.user_id))
            row = cur.fetchone()
            
            if not row:
                interval, ease_factor, reps = 0, 2.5, 0
            else:
                interval, ease_factor, reps = row
                
            # Алгоритм SM-2
            if rating >= 3:
                if reps == 0:
                    interval = 1
                elif reps == 1:
                    interval = 6
                else:
                    interval = round(interval * ease_factor)
                
                reps += 1
                ease_factor = ease_factor + (0.1 - (5 - rating) * (0.08 + (5 - rating) * 0.02))
            else:
                reps = 0
                interval = 1
                ease_factor = max(1.3, ease_factor - 0.2)
                
            ease_factor = max(1.3, ease_factor)
            next_review = datetime.now() + timedelta(days=interval)
            
            cur.execute("""
                INSERT INTO user_words (user_id, word_id, interval, ease_factor, reps, next_review, status)
                VALUES (%s, %s, %s, %s, %s, %s, 'learning')
                ON CONFLICT (user_id, word_id) DO UPDATE SET
                    interval = EXCLUDED.interval,
                    ease_factor = EXCLUDED.ease_factor,
                    reps = EXCLUDED.reps,
                    next_review = EXCLUDED.next_review,
                    status = 'learning'
            """, (request.user_id, word_id, interval, ease_factor, reps, next_review))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@trainer_bp.route('/stats', methods=['GET'])
@token_required
def get_stats():
    """Статистика по изучению слов"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Общее кол-во слов в базе по уровням
        cur.execute("SELECT level, COUNT(*) FROM words GROUP BY level")
        total_by_level = dict(cur.fetchall())
        
        # Кол-во слов в разных статусах (learning, known)
        cur.execute("SELECT status, COUNT(*) FROM user_words WHERE user_id = %s GROUP BY status", (request.user_id,))
        user_status_counts = dict(cur.fetchall())
        
        # Детально по уровням для пользователя
        cur.execute("""
            SELECT w.level, uw.status, COUNT(*) 
            FROM user_words uw
            JOIN words w ON uw.word_id = w.id
            WHERE uw.user_id = %s
            GROUP BY w.level, uw.status
        """, (request.user_id,))
        
        user_detailed = []
        for row in cur.fetchall():
            user_detailed.append({
                "level": row[0],
                "status": row[1],
                "count": row[2]
            })
            
        cur.close()
        conn.close()
        
        return jsonify({
            "total_words": total_by_level,
            "user_progress": user_status_counts,
            "detailed": user_detailed
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
