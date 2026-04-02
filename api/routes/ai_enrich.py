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

# Промпт усилен для лингвистической точности и богатства контента
PROMPT_TEMPLATE = """Ты — эксперт-лингвист немецкого языка. Твоя задача — предоставить богатые и точные данные для учебного приложения.

Слово: {de}
Предполагаемый перевод: {ru}
Артикль (подсказка): {article}

ИНСТРУКЦИИ ПО КОНТЕНТУ:
1. ПЕРЕВОД (ru): Дай точный перевод. Если у слова есть несколько важных значений, укажи их через запятую.
2. ТЕМА (topic): Определи наиболее подходящую тему.
3. ОМОНИМЫ: Проверь, нет ли у слова разных значений в зависимости от рода.
4. СУЩЕСТВИТЕЛЬНЫЕ: Артикль (der/die/das) + Plural (напр. "die Tische").
5. ГЛАГОЛЫ И ПРИЛАГАТЕЛЬНЫЕ: Для них ПОЛЯ "article" и "plural" ДОЛЖНЫ БЫТЬ ПУСТЫМИ СТРОКАМИ ("").
6. ГЛАГОЛЫ: 4 формы через запятую: "Infinitiv, Präsens(3sg), Präteritum(3sg), Partizip II".
7. СИНОНИМЫ/АНТОНИМЫ: Приведи ровно по 3 наиболее употребимых.
8. КОЛЛОКАЦИИ (collocations): Приведи 3-5 устойчивых сочетаний.

Формат ответа — СТРОГО JSON:
{{
  "ru": "перевод",
  "article": "der|die|das| (ТОЛЬКО для сущ, иначе \"\")",
  "plural": "die ... (ТОЛЬКО для сущ, иначе \"\")",
  "level": "A1|A2|B1|B2|C1",
  "topic": "Тема",
  "verb_forms": "Infinitiv, Präsens, Präteritum, Partizip II (ТОЛЬКО для глаголов, иначе \"\")",
  "synonyms": "син1, син2, син3",
  "antonyms": "ант1, ант2, ант3",
  "collocations": "фраза1, фраза2, фраза3",
  "examples": [
    {{"de": "...", "ru": "..."}},
    {{"de": "...", "ru": "..."}},
    {{"de": "...", "ru": "..."}}
  ]
}}
"""

def _parse_ai_response(text: str) -> AIWordData:
    """Парсим и валидируем ответ от AI с помощью Pydantic."""
    text = text.strip()
    if "```" in text:
        try:
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            else:
                text = text.split("```")[1].split("```")[0]
        except IndexError:
            pass
    text = text.strip()
    
    try:
        return AIWordData.model_validate_json(text)
    except ValidationError as e:
        logger.error(f"Pydantic Validation Error: {e.json()}")
        raise ValueError(f"AI вернул некорректную структуру: {e.errors()[0]['msg']}")
    except Exception as e:
        logger.error(f"JSON Parsing Error: {str(e)}")
        raise ValueError(f"Ошибка парсинга JSON: {str(e)}")

def _try_groq(prompt: str) -> AIWordData:
    from openai import OpenAI
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key: raise RuntimeError("GROQ_API_KEY missing")

    client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
    models = ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"]
    
    for model_name in models:
        try:
            resp = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            return _parse_ai_response(resp.choices[0].message.content)
        except Exception as e:
            logger.warning(f"Groq {model_name} failed: {e}")
            continue
    raise RuntimeError("Groq unavailable")

def _try_gemini(prompt: str) -> AIWordData:
    import google.generativeai as genai
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key: raise RuntimeError("GEMINI_API_KEY missing")

    genai.configure(api_key=api_key)
    for model_name in ["gemini-1.5-flash", "gemini-1.5-pro"]:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json", "temperature": 0.1})
            return _parse_ai_response(response.text)
        except Exception as e:
            logger.warning(f"Gemini {model_name} failed: {e}")
            continue
    raise RuntimeError("Gemini unavailable")

@ai_enrich_bp.route('/words/ai-enrich', methods=['POST'])
@token_required
def ai_enrich():
    """Обогатить данные о немецком слове с помощью усиленного AI-анализа."""
    try:
        data = request.json or {}
        # Используем существующую схему запроса, но добавим опциональный артикль
        de = data.get('de', '').strip()
        ru = data.get('ru', '').strip()
        article_hint = data.get('article', '').strip() # Подсказка по артиклю

        if not de:
            return jsonify({"error": "Поле 'de' обязательно"}), 400

        # Формируем промпт с подсказками для точности
        prompt = PROMPT_TEMPLATE.format(
            de=de, 
            ru=ru if ru else "определи автоматически",
            article=article_hint if article_hint else "определи автоматически",
            level_hint="A1-B1"
        )
        
        result = None
        errors = []
        for provider_fn in [_try_groq, _try_gemini]:
            try:
                result = provider_fn(prompt)
                if result: break
            except Exception as e:
                errors.append(str(e))
                continue

        if not result:
            return jsonify({"error": "AI-провайдеры недоступны", "details": errors}), 503

        # Если пользователь давал подсказку по артиклю, и AI ее проигнорировал (маловероятно, но всё же)
        # мы можем либо доверять AI, либо принудительно ставить артикль пользователя.
        # Оставим результат AI, так как промпт теперь жестко требует учитывать подсказку.

        return jsonify(result.model_dump()), 200

    except Exception as e:
        logger.error(f"AI Enrich Error: {str(e)}")
        return jsonify({"error": str(e)}), 500
