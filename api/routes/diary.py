from flask import Blueprint, request, jsonify
import os
import google.generativeai as genai
from openai import OpenAI
from dotenv import load_dotenv

diary_bp = Blueprint('diary', __name__, url_prefix='/api/diary')

# Загружаем переменные окружения
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env.local')
load_dotenv(env_path)

def correct_with_gemini(text):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "Ваш_Ключ_Здесь":
        return None, "GEMINI_API_KEY не настроен"
    
    try:
        genai.configure(api_key=api_key)
        # Пробуем более стабильное имя модели
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Для отладки
        print(f"Попытка исправления текста через Gemini: {text[:30]}...")
        Ты — помощник по изучению немецкого языка. 
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
        return None, str(e)

@diary_bp.route('/correct', methods=['POST'])
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
    
    return jsonify(result), 200
