from flask import Blueprint, request, jsonify
import os
import json
import sys
import logging
from pydantic import ValidationError

api_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)

from .auth import token_required
from schemas import AIWordData, AIEnrichRequest

ai_enrich_bp = Blueprint('ai_enrich', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)

# Промпт теперь более строгий и включает описание JSON схемы
PROMPT_TEMPLATE = """Ты — эксперт по немецкому языку. Проанализируй слово и верни результат в формате JSON.

Слово: {de}
Перевод: {ru}

Твой ответ должен быть СТРОГО валидным JSON-объектом со следующей структурой:
{{
  "article": "der", "die", "das" или "" (только для существительных),
  "level": "A1", "A2", "B1", "B2" или "C1",
  "verb_forms": "Infinitiv, Präteritum, Partizip II" (ТОЛЬКО для глаголов, иначе ""),
  "examples": [
    {{"de": "Пример предложения на немецком", "ru": "Перевод на русский"}},
    ... (2-3 примера)
  ]
}}

Правила:
- Уровень должен соответствовать сложности слова.
- Примеры должны быть короткими и полезными.
- Не добавляй никакого текста кроме JSON.
"""

def _parse_ai_response(text: str) -> AIWordData:
    """Парсим и валидируем ответ от AI с помощью Pydantic."""
    text = text.strip()
    
    # Очистка от markdown-блоков ```json ... ```
    if "```" in text:
        # Извлекаем содержимое между первыми и последними бэктриками
        try:
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            else:
                text = text.split("```")[1].split("```")[0]
        except IndexError:
            pass
    
    text = text.strip()
    
    try:
        # Используем Pydantic для валидации структуры
        return AIWordData.model_validate_json(text)
    except ValidationError as e:
        logger.error(f"Pydantic Validation Error: {e.json()}")
        raise ValueError(f"AI вернул данные в неверном формате: {e}")
    except Exception as e:
        logger.error(f"JSON Parsing Error: {str(e)}")
        raise ValueError(f"Не удалось распарсить JSON: {str(e)}")

def _try_groq(prompt: str) -> AIWordData:
    """Пробуем Groq (Llama 3 или Mixtral)."""
    from openai import OpenAI

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY не задан")

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1"
    )
    
    # Рекомендуемые модели Groq
    models = ["llama-3.3-70b-versatile", "llama3-8b-8192", "mixtral-8x7b-32768"]
    
    for model_name in models:
        try:
            logger.info(f"Trying Groq model: {model_name}")
            resp = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1, # Низкая температура для стабильности JSON
                max_tokens=1000,
                response_format={"type": "json_object"} if "llama" in model_name.lower() else None
            )
            return _parse_ai_response(resp.choices[0].message.content)
        except Exception as e:
            logger.warning(f"Groq {model_name} failed: {str(e)}")
            continue
            
    raise RuntimeError("Все модели Groq недоступны")

def _try_gemini(prompt: str) -> AIWordData:
    """Пробуем Gemini (запасной вариант)."""
    import google.generativeai as genai

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY не задан")

    genai.configure(api_key=api_key)
    
    models = ["gemini-1.5-flash", "gemini-1.5-pro"]
    
    for model_name in models:
        try:
            logger.info(f"Trying Gemini model: {model_name}")
            model = genai.GenerativeModel(model_name)
            
            # Настройка для генерации JSON
            generation_config = genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.1
            )
            
            response = model.generate_content(prompt, generation_config=generation_config)
            return _parse_ai_response(response.text)
        except Exception as e:
            logger.warning(f"Gemini {model_name} failed: {str(e)}")
            continue
            
    raise RuntimeError("Все модели Gemini недоступны")

@ai_enrich_bp.route('/words/ai-enrich', methods=['POST'])
@token_required
def ai_enrich():
    """Обогатить данные о немецком слове с помощью AI."""
    try:
        # Валидация входных данных через Pydantic
        try:
            enrich_req = AIEnrichRequest.model_validate(request.json or {})
        except ValidationError as e:
            return jsonify({"error": "Неверные входные данные", "details": e.errors()}), 400

        de = enrich_req.de
        ru = enrich_req.ru or ""

        prompt = PROMPT_TEMPLATE.format(de=de, ru=ru)
        
        # Пробуем провайдеров по очереди
        result = None
        errors = []
        
        for provider_fn in [_try_groq, _try_gemini]:
            try:
                result = provider_fn(prompt)
                if result:
                    break
            except Exception as e:
                errors.append(f"{provider_fn.__name__}: {str(e)}")
                continue

        if not result:
            return jsonify({
                "error": "Не удалось получить данные от AI",
                "details": " | ".join(errors)
            }), 503

        # Возвращаем валидированные данные
        return jsonify(result.model_dump()), 200

    except Exception as e:
        logger.error(f"AI Enrich General Error: {str(e)}")
        return jsonify({"error": f"Ошибка сервиса: {str(e)}"}), 500
