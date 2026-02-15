from flask import Blueprint, request, jsonify
from datetime import datetime
import os
import sys

# Добавляем родительскую директорию в path
api_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)

from db import get_db_connection

audio_bp = Blueprint('audio', __name__, url_prefix='/api')

# Директория для загрузок - используем постоянное хранилище
UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join(os.path.dirname(__file__), "uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Константы безопасности
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {'webm', 'mp3', 'wav', 'ogg'}

def allowed_file(filename: str) -> bool:
    """Проверка расширения файла"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@audio_bp.route('/audio', methods=['POST'])
def upload_audio():
    """Загрузка аудиофайла"""
    try:
        file = request.files.get("file")
        if not file or file.filename == '':
            print("Ошибка: файл не выбран")
            return jsonify({"error": "Файл не выбран"}), 400
        
        print(f"Получен файл: {file.filename}")
        
        # Проверяем расширение
        if not allowed_file(file.filename):
            print(f"Ошибка: недопустимое расширение {file.filename}")
            return jsonify({"error": "Недопустимый формат файла"}), 400
        
        # Проверяем размер
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        print(f"Размер файла: {file_size} байт")
        
        if file_size > MAX_FILE_SIZE:
            print(f"Ошибка: файл слишком большой ({file_size} > {MAX_FILE_SIZE})")
            return jsonify({"error": "Файл слишком большой"}), 413
        file.seek(0)
        
        # Сохраняем файл с безопасным именем
        filename = datetime.now().strftime("%Y%m%d-%H%M%S") + ".webm"
        filepath = os.path.join(UPLOAD_DIR, filename)
        file.save(filepath)
        
        # Проверяем, что файл действительно сохранен
        saved_size = os.path.getsize(filepath)
        print(f"Файл сохранен: {filename} ({saved_size} байт)")
        
        return jsonify({"status": "ok", "filename": filename, "size": saved_size}), 201
    
    except Exception as e:
        print(f"Исключение при загрузке: {str(e)}")
        return jsonify({"error": str(e)}), 500

@audio_bp.route('/list_audio', methods=['GET'])
def list_audio():
    """Получить список всех аудиофайлов"""
    try:
        if os.path.exists(UPLOAD_DIR):
            files = sorted(os.listdir(UPLOAD_DIR), reverse=True)
            files = [f for f in files if allowed_file(f)]
        else:
            files = []
        return jsonify(files), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@audio_bp.route('/delete_audio', methods=['POST'])
def delete_audio():
    """Удалить аудиофайл"""
    try:
        data = request.get_json()
        filename = data.get("filename")
        
        if not filename:
            return jsonify({"error": "Имя файла не указано"}), 400
        
        # Безопасность: проверяем, что файл в нужной директории
        filepath = os.path.join(UPLOAD_DIR, filename)
        if not os.path.abspath(filepath).startswith(os.path.abspath(UPLOAD_DIR)):
            return jsonify({"error": "Доступ запрещён"}), 403
        
        if os.path.exists(filepath):
            os.remove(filepath)
            return jsonify({"status": "deleted"}), 200
        else:
            return jsonify({"error": "Файл не найден"}), 404
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@audio_bp.route('/files/<path:filename>', methods=['GET'])
def serve_file(filename):
    """Скачать аудиофайл"""
    from flask import send_from_directory
    try:
        # Безопасность: проверяем путь
        filepath = os.path.join(UPLOAD_DIR, filename)
        if not os.path.abspath(filepath).startswith(os.path.abspath(UPLOAD_DIR)):
            return jsonify({"error": "Доступ запрещён"}), 403
        
        return send_from_directory(UPLOAD_DIR, filename), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
