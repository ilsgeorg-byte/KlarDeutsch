from flask import Blueprint, request, jsonify
import os
import json
import sys

api_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)

from .auth import token_required

ai_enrich_bp = Blueprint('ai_enrich', __name__, url_prefix='/api')


def get_gemini_answer(de: str, ru: str) -> dict:
    """Запрашиваем у Gemini данные о немецком слове."""
    import google.generativeai as genai

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY не задан в окружении")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")

    prompt = f"""Ты — эксперт по немецкому языку. Проанализируй слово и верни JSON.

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

    response = model.generate_content(prompt)
    text = response.text.strip()

    # Убираем markdown-обёртки если есть
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if lines[-1] == "```" else "\n".join(lines[1:])

    return json.loads(text)


@ai_enrich_bp.route('/words/ai-enrich', methods=['POST'])
@token_required
def ai_enrich():
    """Обогатить данные о немецком слове с помощью Gemini AI."""
    try:
        data = request.json or {}
        de = data.get('de', '').strip()
        ru = data.get('ru', '').strip()

        if not de:
            return jsonify({"error": "Поле 'de' обязательно"}), 400

        result = get_gemini_answer(de, ru)

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
