from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from datetime import datetime

# ... импорт WORDS ...
from data_words import WORDS

app = Flask(__name__)
CORS(app)

# Папка для аудио. Важно: для локального доступа она должна быть вне /tmp, если хочешь сохранять надолго.
# Но Vercel удаляет файлы после перезапуска. Локально используем папку uploads в корне API.
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.route("/", methods=["GET", "POST", "DELETE"])
def handler():
    action = request.args.get("action", "words")

    # 1. Слова
    if action == "words" and request.method == "GET":
        level = request.args.get("level", "A1")
        return jsonify([w for w in WORDS if w["level"] == level])

    # 2. Загрузка аудио
    if action == "audio" and request.method == "POST":
        file = request.files.get("file")
        if not file: return jsonify({"error": "no file"}), 400
        
        # Очистка старых файлов если их больше 50 (чтобы память не забивать)
        files = sorted(os.listdir(UPLOAD_DIR))
        if len(files) > 50:
            os.remove(os.path.join(UPLOAD_DIR, files[0]))

        filename = datetime.now().strftime("%Y%m%d-%H%M%S") + ".webm"
        file.save(os.path.join(UPLOAD_DIR, filename))
        return jsonify({"status": "ok", "filename": filename})

    # 3. Список файлов
    if action == "list_audio" and request.method == "GET":
        files = sorted(os.listdir(UPLOAD_DIR), reverse=True)
        return jsonify(files)

    # 4. Удаление файла
    if action == "delete_audio" and request.method == "POST":
        filename = request.json.get("filename")
        try:
            os.remove(os.path.join(UPLOAD_DIR, filename))
            return jsonify({"status": "deleted"})
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    return jsonify({"error": "unknown action"}), 400

# Отдельный роут для скачивания/прослушивания файла
# Vercel требует отдельный путь или send_from_directory
@app.route("/files/<path:filename>")
def serve_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
