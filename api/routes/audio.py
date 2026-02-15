from flask import Blueprint, request, jsonify
from datetime import datetime
import os
import sys
import boto3

# Добавляем родительскую директорию в path
api_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)

from db import get_db_connection

audio_bp = Blueprint('audio', __name__, url_prefix='/api')

# S3 Configuration
S3_BUCKET = os.getenv("S3_BUCKET")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_REGION = os.getenv("S3_REGION", "us-east-1")

def get_s3_client():
    return boto3.client(
        's3', aws_access_key_id=S3_ACCESS_KEY, aws_secret_access_key=S3_SECRET_KEY,
        region_name=S3_REGION, endpoint_url=S3_ENDPOINT
    )

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
            return jsonify({"error": "Файл не выбран"}), 400
        
        # Проверяем расширение
        if not allowed_file(file.filename):
            return jsonify({"error": "Недопустимый формат файла"}), 400
        
        # Проверяем размер
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({"error": "Файл слишком большой"}), 413
        
        # Генерируем имя и загружаем в S3
        filename = datetime.now().strftime("%Y%m%d-%H%M%S") + "_" + file.filename
        content_type = file.content_type or 'application/octet-stream'

        s3 = get_s3_client()
        s3.upload_fileobj(
            file, S3_BUCKET, filename,
            ExtraArgs={'ContentType': content_type, 'ACL': 'public-read'}
        )
        
        # Формируем URL
        if S3_ENDPOINT:
             url = f"{S3_ENDPOINT}/{S3_BUCKET}/{filename}"
        else:
             url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{filename}"
        
        # Сохраняем в БД
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Создаем таблицу если нет (для надежности, лучше вынести в миграции)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS recordings (
                id SERIAL PRIMARY KEY,
                filename TEXT NOT NULL,
                url TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cur.execute("INSERT INTO recordings (filename, url) VALUES (%s, %s) RETURNING id", (filename, url))
        record_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({"status": "ok", "url": url, "id": record_id}), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@audio_bp.route('/list_audio', methods=['GET'])
def list_audio():
    """Получить список всех аудиофайлов"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Проверяем существование таблицы
        cur.execute("SELECT to_regclass('public.recordings')")
        if not cur.fetchone()[0]:
             return jsonify([]), 200

        cur.execute("SELECT filename, url, created_at FROM recordings ORDER BY created_at DESC")
        rows = cur.fetchall()
        files = [{"filename": r[0], "url": r[1], "created_at": r[2]} for r in rows]
        
        cur.close()
        conn.close()
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
        
        # Удаляем из S3
        s3 = get_s3_client()
        s3.delete_object(Bucket=S3_BUCKET, Key=filename)
        
        # Удаляем из БД
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM recordings WHERE filename = %s", (filename,))
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({"status": "deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
