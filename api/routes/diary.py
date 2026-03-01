from flask import Blueprint, request, jsonify
import os
import sys
import logging
import google.generativeai as genai
from openai import OpenAI
from .auth import token_required
from db import get_db_connection

diary_bp = Blueprint('diary', __name__, url_prefix='/api/diary')

# Логгер
logger = logging.getLogger(__name__)

# Переменные окружения уже загружены в index.py

def correct_with_gemini(text):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "Ваш_Ключ_Здесь":
        return None, "GEMINI_API_KEY не настроен"
    
    try:
        genai.configure(api_key=api_key)
        
        # Динамический поиск доступной модели
        available_models = []
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available_models.append(m.name)
        except Exception as list_err:
            print(f"Ошибка при получении списка моделей: {list_err}")

        # Пытаемся выбрать лучшую из доступных
        model_name = None
        # Приоритет 1: gemini-1.5-flash (имена могут начинаться с models/)
        for m in available_models:
            if 'gemini-1.5-flash' in m:
                model_name = m
                break
        
        # Приоритет 2: любая 1.5 модель
        if not model_name:
            for m in available_models:
                if 'gemini-1.5' in m:
                    model_name = m
                    break
        
        # Приоритет 3: любая gemini модель
        if not model_name:
            for m in available_models:
                if 'gemini' in m:
                    model_name = m
                    break

        if not model_name:
            models_list_str = ", ".join(available_models) if available_models else "None"
            return None, f"Не найдено подходящих моделей Gemini. Доступно: {models_list_str}. Проверьте лимиты вашего API ключа."

        print(f"Используем модель: {model_name}")
        model = genai.GenerativeModel(model_name)
        
        prompt = f"""
        Ты - помощник по изучению немецкого языка. 
        Исправь грамматические и стилистические ошибки в следующем тексте на немецком языке.
        Текст: "{text}"
        
        Верни ответ строго в формате JSON:
        {{
          "corrected": "исправленный текст",
          "explanation": "краткое объяснение исправлений на русском языке"
        }}
        """
        
        response = model.generate_content(prompt)
        # Очистка от markdown если есть
        content = response.text.strip()
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("{") and content.endswith("}"):
            pass
        else:
            # Пытаемся найти JSON внутри текста
            import re
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                content = match.group()
        
        import json
        return json.loads(content), None
    except Exception as e:
        print(f"Gemini Error: {str(e)}")
        return None, str(e)

def correct_with_openai(text):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None, "OPENAI_API_KEY не настроен"
    
    try:
        client = OpenAI(api_key=api_key)
        
        prompt = f"""
        Ты — помощник по изучению немецкого языка. 
        Исправь грамматические и стилистические ошибки в следующем тексте на немецком языке.
        Текст: "{text}"
        
        Верни ответ строго в формате JSON:
        {{
          "corrected": "исправленный текст",
          "explanation": "краткое объяснение исправлений на русском языке"
        }}
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        
        import json
        return json.loads(response.choices[0].message.content), None
    except Exception as e:
        print(f"OpenAI Error: {str(e)}")
        return None, str(e)

@diary_bp.route('/correct', methods=['POST'])
@token_required
def correct_text():
    data = request.get_json()
    text = data.get("text", "")
    
    if not text:
        return jsonify({"error": "Текст не может быть пустым"}), 400
    
    # Сначала пробуем Gemini, потом OpenAI
    result, error = correct_with_gemini(text)
    
    if error and "GEMINI_API_KEY не настроен" in error:
        result, error = correct_with_openai(text)
        
    if error:
        # Если оба не сработали
        if "API_KEY не настроен" in error:
             return jsonify({
                 "error": "AI-ключи не настроены. Для работы дневника добавьте GEMINI_API_KEY в настройки (Vercel Environment Variables или .env.local)."
             }), 500
        return jsonify({"error": f"Ошибка AI: {error}"}), 500
    
    # СОХРАНЕНИЕ В БД
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO diary_entries (user_id, original_text, corrected_text, explanation)
            VALUES (%s, %s, %s, %s)
        """, (request.user_id, text, result['corrected'], result['explanation']))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as db_err:
        print(f"Ошибка сохранения в БД: {db_err}")
        # Не возвращаем ошибку пользователю, так как коррекция уже получена
    
    return jsonify(result), 200

@diary_bp.route('/history', methods=['GET'])
@token_required
def get_history():
    """Получить историю записей"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, original_text, corrected_text, explanation, created_at
            FROM diary_entries
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (request.user_id,))
        
        columns = [desc[0] for desc in cur.description]
        results = []
        for row in cur.fetchall():
            item = dict(zip(columns, row))
            # Форматируем дату для фронтенда
            if item['created_at']:
                item['created_at'] = item['created_at'].strftime("%Y-%m-%d %H:%M")
            results.append(item)
            
        cur.close()
        conn.close()
        return jsonify(results), 200
    except Exception as e:
        print(f"History Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@diary_bp.route('/history/<int:entry_id>', methods=['DELETE'])
@token_required
def delete_entry(entry_id):
    """Удалить запись из истории"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM diary_entries WHERE id = %s AND user_id = %s", (entry_id, request.user_id))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Delete Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@diary_bp.route('/extract-words', methods=['POST'])
@token_required
def extract_words():
    """Извлечь слова из исправления для добавления в тренажер"""
    try:
        data = request.json
        original = data.get('original')
        corrected = data.get('corrected')
        
        prompt = f"""
        Extract the most important German words from this correction that a student should learn.
        Original: {original}
        Corrected: {corrected}
        
        Return ONLY a JSON list of objects:
        [
          {{"de": "Wort", "ru": "Слово", "article": "der/die/das", "level": "A1/A2/B1"}}
        ]
        If no important words, return empty list [].
        """
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        text = response.text.replace('```json', '').replace('```', '').strip()
        
        import json
        import re
        json_match = re.search(r'\[.*\]', text, re.DOTALL)
        if json_match:
            words = json.loads(json_match.group(0))
        else:
            words = []
            
        return jsonify(words), 200
    except Exception as e:
        print(f"Extraction Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@diary_bp.route('/add-words', methods=['POST'])
@token_required
def add_diary_words():
    """Добавить слова из дневника напрямую в тренажер"""
    try:
        words = request.json # Список объектов {{de, ru, article, level}}
        if not words:
            return jsonify({{"status": "ok"}}), 200
            
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Сначала убедимся, что есть индекс для ON CONFLICT
        # cur.execute("ALTER TABLE words ADD CONSTRAINT unique_word UNIQUE (de, ru);") # Это лучше сделать в init_db
        
        added_count = 0
        for w in words:
            # 1. Добавляем в общую базу слов (через дедукцию ID)
            cur.execute("""
                INSERT INTO words (de, ru, article, level, topic)
                VALUES (%s, %s, %s, %s, 'Дневник')
                ON CONFLICT (de, ru) DO UPDATE SET de = EXCLUDED.de
                RETURNING id
            """, (w['de'], w['ru'], w.get('article', ''), w.get('level', 'A1')))
            
            row = cur.fetchone()
            word_id = row[0] if row else None
                
            if word_id:
                # 2. Добавляем в список изучения пользователя
                cur.execute("""
                    INSERT INTO user_words (user_id, word_id, status, next_review)
                    VALUES (%s, %s, 'learning', CURRENT_TIMESTAMP)
                    ON CONFLICT (user_id, word_id) DO NOTHING
                """, (request.user_id, word_id))
                added_count += 1
                
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({"status": "success", "added_count": added_count}), 200
    except Exception as e:
        print(f"Add words error: {e}")
        return jsonify({"error": str(e)}), 500
