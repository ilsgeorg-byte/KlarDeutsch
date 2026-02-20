from flask import Blueprint, request, jsonify
import os
import json
import sys

api_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)

from .auth import token_required

ai_enrich_bp = Blueprint('ai_enrich', __name__, url_prefix='/api')


PROMPT_TEMPLATE = """Ты — эксперт по немецкому языку. Проанализируй слово и верни JSON.

Слово: {de}
Перевод: {ru}

Верни ТОЛЬКО валидный JSON (без markdown, без пояснений):
{{
  "article": "der|die|das или пустую строку если не существительное",
  "level": "A1|A2|B1|B2|C1",
  "verb_forms": "если глагол: Infinitiv, Präteritum 3sg, Partizip II через запятую. Иначе пустая строка",
  "examples": [
    {{"de": "Пример 1 на немецком.", "ru": "Перевод примера 1."}},
    {{"de": "Пример 2 на немецком.", "ru": "Перевод примера 2."}},
    {{"de": "Пример 3 на немецком.", "ru": "Перевод примера 3."}}
  ]
}}

Правила:
- article: пустая строка для глаголов, прилагательных, наречий
- verb_forms: заполняй ТОЛЬКО для глаголов (напр. "machen, machte, hat gemacht")
- examples: 2-3 коротких практичных примера уровня A1-B1
- Весь JSON должен быть валидным, без комментариев
"""


def _parse_json_response(text: str) -> dict:
    """Парсим JSON-ответ, убирая возможные markdown-обёртки."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        inner = lines[1:]
        if inner and inner[-1].strip() == "```":
            inner = inner[:-1]
        text = "\n".join(inner)
    return json.loads(text)


def _try_groq(prompt: str) -> dict:
    """Пробуем Groq (бесплатный, быстрый)."""
    from openai import OpenAI

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY не задан")

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1"
    )
    # Пробуем модели Groq по очереди
    for model_name in ["llama-3.3-70b-versatile", "llama3-8b-8192", "mixtral-8x7b-32768"]:
        try:
            resp = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=800,
            )
            return _parse_json_response(resp.choices[0].message.content)
        except Exception as e:
            err = str(e)
            if "404" in err or "model" in err.lower():
                continue
            raise
    raise RuntimeError("Ни одна модель Groq не доступна")


def _try_gemini(prompt: str) -> dict:
    """Пробуем Gemini как запасной вариант."""
    import google.generativeai as genai

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY не задан")

    genai.configure(api_key=api_key)
    for model_name in ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-pro"]:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return _parse_json_response(response.text)
        except Exception as e:
            err = str(e)
            if "429" in err or "404" in err or "quota" in err.lower() or "not found" in err.lower():
                continue
            raise
    raise RuntimeError("Все модели Gemini недоступны или исчерпана квота")


def get_ai_word_data(de: str, ru: str) -> dict:
    """Пробуем Groq → Gemini. Возвращает dict с article/level/verb_forms/examples."""
    prompt = PROMPT_TEMPLATE.format(de=de, ru=ru)

    errors = []
    for provider_fn in [_try_groq, _try_gemini]:
        try:
            return provider_fn(prompt)
        except Exception as e:
            errors.append(str(e))
            continue

    raise RuntimeError("Все AI-провайдеры недоступны: " + " | ".join(errors))


@ai_enrich_bp.route('/words/ai-enrich', methods=['POST'])
@token_required
def ai_enrich():
    """Обогатить данные о немецком слове с помощью AI."""
    try:
        data = request.json or {}
        de = data.get('de', '').strip()
        ru = data.get('ru', '').strip()

        if not de:
            return jsonify({"error": "Поле 'de' обязательно"}), 400

        result = get_ai_word_data(de, ru)

        return jsonify({
            "article": result.get("article", ""),
            "level": result.get("level", "A1"),
            "verb_forms": result.get("verb_forms", ""),
            "examples": result.get("examples", [])
        }), 200

    except json.JSONDecodeError as e:
        return jsonify({"error": f"AI вернул некорректный JSON: {str(e)}"}), 500
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": f"Ошибка AI: {str(e)}"}), 500
