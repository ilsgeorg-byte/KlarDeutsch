from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import os
import sys
import logging
import random

# Добавляем родительскую директорию в path
api_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)

from .auth import token_required
from db import get_db_connection
from schemas import TrainingQuery, RateWordRequest, VALID_LEVELS

trainer_bp = Blueprint('trainer', __name__, url_prefix='/api/trainer')

# Логгер
logger = logging.getLogger(__name__)

# === Настройки алгоритма SM-2 ===
# Fuzzing - случайный разброс интервала (в процентах)
FUZZING_FACTOR = 0.1  # ±10% от интервала

# Минимальный интервал для "Сложно" (в минутах)
MIN_INTERVAL_MINUTES = 10

# Множитель снижения ease_factor для "Сложно"
EASE_PENALTY_HARD = 0.3  # Агрессивнее стандартного 0.2


@trainer_bp.route('/words', methods=['GET'])
@token_required
def get_training_words():
    """
    Получить слова для тренировки:
    1. Слова, которые пора повторить (next_review <= now)
    2. Новые слова из выбранного уровня (которых еще нет в user_words)
    """
    try:
        # Валидация через Pydantic
        query = TrainingQuery(
            level=request.args.get("level", "A1").upper(),
            limit=int(request.args.get("limit", 10))
        )

        logger.info(f"Запрос слов для пользователя {request.user_id}, уровень: {query.level}, лимит: {query.limit}")

        # Определяем список уровней для выборки (кумулятивно)
        all_levels = ["A1", "A2", "B1", "B2", "C1"]
        if query.level in all_levels:
            target_levels = all_levels[:all_levels.index(query.level) + 1]
        else:
            target_levels = [query.level]

        conn = get_db_connection()
        cur = conn.cursor()

        # 1. Получаем слова, которые пора повторить
        logger.info(f"Выполняем запрос на повторение: user_id={request.user_id}, levels={target_levels}")
        cur.execute("""
            SELECT w.id, w.level, w.topic, w.de, w.ru, w.article, w.example_de, w.example_ru,
                   uw.interval, uw.ease_factor, uw.reps, uw.next_review
            FROM words w
            JOIN user_words uw ON w.id = uw.word_id
            WHERE w.level IN %s AND uw.user_id = %s AND uw.next_review <= CURRENT_TIMESTAMP AND uw.status = 'learning'
            ORDER BY uw.next_review ASC
            LIMIT %s
        """, (tuple(target_levels), request.user_id, query.limit))

        columns = [desc[0] for desc in cur.description]
        cards_to_review = [dict(zip(columns, row)) for row in cur.fetchall()]
        logger.info(f"Найдено слов на повторение: {len(cards_to_review)}")
        
        # 2. Если слов меньше лимита, добавляем новые
        remaining = query.limit - len(cards_to_review)
        if remaining > 0:
            logger.info(f"Добавляем {remaining} новых слов")
            cur.execute("""
                SELECT w.id, w.level, w.topic, w.de, w.ru, w.article, w.example_de, w.example_ru
                FROM words w
                LEFT JOIN user_words uw ON w.id = uw.word_id AND uw.user_id = %s
                WHERE w.level IN %s AND uw.word_id IS NULL
                ORDER BY RANDOM()
                LIMIT %s
            """, (request.user_id, tuple(target_levels), remaining))

            columns = [desc[0] for desc in cur.description]
            new_words = [dict(zip(columns, row)) for row in cur.fetchall()]
            logger.info(f"Найдено новых слов: {len(new_words)}")
            cards_to_review.extend(new_words)
        else:
            logger.info(f"Новые слова не требуются (уже есть {len(cards_to_review)})")

        cur.close()
        conn.close()

        logger.info(f"Возвращаем {len(cards_to_review)} слов")
        return jsonify(cards_to_review), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@trainer_bp.route('/rate', methods=['POST'])
@token_required
def rate_word():
    """
    Обновить прогресс слова по улучшенному алгоритму SM-2
    
    Rating:
    - 0: Знаю (убрать из колоды)
    - 1: Сложно (повтор через 10 минут)
    - 3: Хорошо (стандартный интервал)
    - 5: Легко (увеличенный интервал)
    
    Улучшения:
    - Fuzzing: случайный разброс интервала для предотвращения "куч"
    - Агрессивное снижение ease_factor для "Сложно"
    - Минимальный интервал 10 минут для внутридневных сессий
    """
    try:
        # Валидация через Pydantic
        try:
            rate_data = RateWordRequest.model_validate(request.json or {})
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        
        word_id = rate_data.word_id
        rating = rate_data.rating

        conn = get_db_connection()
        cur = conn.cursor()

        if rating == 0:
            # Пометить как "известное" навсегда
            logger.info(f"Слово {word_id} помечено как 'known'")
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

            # === Улучшенный алгоритм SM-2 ===
            
            if rating == 1:
                # "Сложно" - агрессивное снижение
                reps = 0
                interval = 0  # 0 дней = повтор через 10 минут
                ease_factor = max(1.3, ease_factor - EASE_PENALTY_HARD)
                logger.info(f"Слово {word_id}: сложно, interval=0 (10 мин), ease_factor={ease_factor:.2f}")
                
            elif rating >= 3:
                # "Хорошо" (3) или "Легко" (5)
                if reps == 0:
                    interval = 1  # Первый повтор - 1 день
                elif reps == 1:
                    interval = 6  # Второй повтор - 6 дней
                else:
                    interval = round(interval * ease_factor)
                
                reps += 1
                
                # Модификатор для "Легко" - бонус к ease_factor
                rating_bonus = 0.1 if rating == 5 else 0
                ease_factor = ease_factor + (0.1 - (5 - rating) * (0.08 + (5 - rating) * 0.02)) + rating_bonus
                
                # Применяем fuzzing (случайный разброс)
                if interval > 1:  # Не применяем к интервалам в 1 день
                    fuzz_range = interval * FUZZING_FACTOR
                    fuzz = random.uniform(-fuzz_range, fuzz_range)
                    interval = max(1, round(interval + fuzz))
                
                logger.info(f"Слово {word_id}: rating={rating}, interval={interval} дней, ease_factor={ease_factor:.2f}")
            
            # Ограничиваем ease_factor минимумом
            ease_factor = max(1.3, ease_factor)
            
            # Вычисляем дату следующего повторения
            if interval == 0:
                # "Сложно" - повтор через 10 минут (внутри той же сессии)
                next_review = datetime.now() + timedelta(minutes=MIN_INTERVAL_MINUTES)
            else:
                # Стандартный интервал в днях
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
