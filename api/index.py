from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys

# 1. МАГИЯ: Заставляем Python видеть файлы в папке api
# Это решает проблему "ModuleNotFoundError: No module named 'db'"
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

app = Flask(__name__)
CORS(app)

# 2. Безопасный импорт базы
try:
    from db import get_db_connection
    print("DB module imported successfully")
except ImportError as e:
    print(f"Error importing db: {e}")
    # Если импорт не сработал, попробуем еще раз (для локального запуска)
    try:
        from api.db import get_db_connection
    except ImportError:
        get_db_connection = None

UPLOAD_DIR = "/tmp/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.route("/api/index", methods=["GET", "POST", "DELETE"]) 
@app.route("/", methods=["GET", "POST", "DELETE"])
def main_route():
    # Проверка на случай, если база не подключилась
    if get_db_connection is None:
        return jsonify({"error": "Database module not found"}), 500

    action = request.args.get("action", "words")
    
    # ... дальше твой старый код (try/except, action == 'words' и т.д.) ...


    try:
        # 1. Получить слова (из Postgres!)
        if action == "words" and request.method == "GET":
            level = request.args.get("level", "A1")
            
            conn = get_db_connection()
            cur = conn.cursor()
            # Используем RealDictCursor для JSON-совместимого вывода, если возможно,
            # но psycopg2 по умолчанию возвращает кортежи.
            # Проще собрать словарь вручную:
            cur.execute("""
                SELECT id, level, topic, de, ru, article, example_de, example_ru, audio_url 
                FROM words 
                WHERE level = %s
            """, (level,))
            
            columns = [desc[0] for desc in cur.description]
            results = []
            for row in cur.fetchall():
                results.append(dict(zip(columns, row)))
            
            cur.close()
            conn.close()
            return jsonify(results)

        # 2. Загрузка аудио (остается как было, локально во временную папку)
        if action == "audio" and request.method == "POST":
            file = request.files.get("file")
            if not file: return jsonify({"error": "no file"}), 400
            
            filename = datetime.now().strftime("%Y%m%d-%H%M%S") + ".webm"
            file.save(os.path.join(UPLOAD_DIR, filename))
            return jsonify({"status": "ok", "filename": filename})

        # 3. Список аудио
        if action == "list_audio" and request.method == "GET":
            if os.path.exists(UPLOAD_DIR):
                files = sorted(os.listdir(UPLOAD_DIR), reverse=True)
            else:
                files = []
            return jsonify(files)
            
        # 4. Удаление аудио
        if action == "delete_audio" and request.method == "POST":
            filename = request.json.get("filename")
            try:
                os.remove(os.path.join(UPLOAD_DIR, filename))
                return jsonify({"status": "deleted"})
            except Exception as e:
                return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"error": "unknown action"}), 400

@app.route("/files/<path:filename>")
def serve_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)





if __name__ == "__main__":
    app.run(debug=True)

