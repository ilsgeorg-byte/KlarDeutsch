from flask import Blueprint, request, jsonify, redirect, send_from_directory, send_file
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import sys
import io

# Добавляем родительскую директорию в path
api_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)

from db import get_db_connection

# Попытка импорта boto3 (опционально)
try:
    import boto3
except ImportError:
    boto3 = None

audio_bp = Blueprint('audio', __name__, url_prefix='/api')

# Папка для локальных загрузок
UPLOAD_FOLDER = os.path.join(api_dir, 'uploads')
try:
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
except OSError:
    # Если файловая система доступна только для чтения (например, Vercel), используем /tmp
    UPLOAD_FOLDER = '/tmp/uploads'
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

# S3 Configuration
S3_BUCKET = os.getenv("S3_BUCKET")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_REGION = os.getenv("S3_REGION", "us-east-1")

def get_s3_client():
    if not boto3:
        return None
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
        
        print(f"Загрузка: {file.filename}, размер: {file_size} байт", file=sys.stderr)
        if file_size == 0:
            return jsonify({"error": "Файл пустой (0 байт)"}), 400

        if file_size > MAX_FILE_SIZE:
            return jsonify({"error": "Файл слишком большой"}), 413
        
        # Генерируем имя
        safe_filename = secure_filename(file.filename)
        filename = datetime.now().strftime("%Y%m%d-%H%M%S") + "_" + safe_filename
        
        # Определяем куда сохранять (S3 или локально)
        use_s3 = S3_BUCKET and S3_ACCESS_KEY and S3_SECRET_KEY and boto3
        url = ""
        file_data = None

        if use_s3:
            content_type = file.content_type or 'application/octet-stream'
            s3 = get_s3_client()
            s3.upload_fileobj(
                file, S3_BUCKET, filename,
                ExtraArgs={'ContentType': content_type, 'ACL': 'public-read'}
            )
            if S3_ENDPOINT:
                 url = f"{S3_ENDPOINT}/{S3_BUCKET}/{filename}"
            else:
                 url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{filename}"
        elif os.environ.get("STORAGE_TYPE") == "db":
            # Сохранение в БД (читаем байты)
            file_data = file.read()
            url = f"/api/files/{filename}"
        else:
            # Локальное сохранение
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            url = f"/api/files/{filename}"
        
        # Сохраняем в БД
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Обновленная структура таблицы (добавляем file_data и mimetype если их нет)
        # Примечание: В продакшене лучше использовать миграции (ALTER TABLE)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS recordings (
                id SERIAL PRIMARY KEY,
                filename TEXT NOT NULL,
                url TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_data BYTEA,
                mimetype TEXT
            )
        """)
        
        # Создаем индекс для ускорения сортировки (если нет)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_recordings_created_at ON recordings(created_at DESC)")
        
        # Пытаемся добавить колонки, если таблица старая (грубая миграция)
        try:
            cur.execute("ALTER TABLE recordings ADD COLUMN IF NOT EXISTS file_data BYTEA")
            cur.execute("ALTER TABLE recordings ADD COLUMN IF NOT EXISTS mimetype TEXT")
        except:
            conn.rollback()

        cur.execute("INSERT INTO recordings (filename, url, file_data, mimetype) VALUES (%s, %s, %s, %s) RETURNING id", (filename, url, file_data, file.content_type))
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
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)

        conn = get_db_connection()
        cur = conn.cursor()
        
        # Проверяем существование таблицы
        cur.execute("SELECT to_regclass('public.recordings')")
        if not cur.fetchone()[0]:
             return jsonify([]), 200

        cur.execute("SELECT filename FROM recordings ORDER BY created_at DESC LIMIT %s OFFSET %s", (limit, offset))
        rows = cur.fetchall()
        files = [r[0] for r in rows]
        
        cur.close()
        conn.close()
        return jsonify(files), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@audio_bp.route('/files/<filename>', methods=['GET'])
def get_file(filename):
    """Получить файл (редирект на S3 URL)"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT url, file_data, mimetype FROM recordings WHERE filename = %s", (filename,))
        row = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if row:
            url, file_data, mimetype = row
            
            # Если есть данные в БД, отдаем их напрямую
            if file_data:
                return send_file(io.BytesIO(file_data), mimetype=mimetype or 'audio/webm', as_attachment=False, download_name=filename)

            if url.startswith("http"):
                return redirect(url)
            
        # Если локальный файл или нет в БД, пробуем отдать с диска
        if os.path.exists(os.path.join(UPLOAD_FOLDER, filename)):
            return send_from_directory(UPLOAD_FOLDER, filename)
            
        return jsonify({"error": "Файл не найден"}), 404
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
        
        # Пробуем удалить из S3 (если настроен)
        if S3_BUCKET and boto3:
            try:
                s3 = get_s3_client()
                s3.delete_object(Bucket=S3_BUCKET, Key=filename)
            except:
                pass # Игнорируем ошибки S3 если файла там нет
        
        # Удаляем локально
        local_path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(local_path):
            os.remove(local_path)

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

@audio_bp.route('/stats', methods=['GET'])
def get_stats():
    """Получить статистику (количество записей и слов)"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Количество записей
        cur.execute("SELECT COUNT(*) FROM recordings")
        recordings_count = cur.fetchone()[0]
        
        # Количество слов (если таблица words существует)
        words_count = 0
        cur.execute("SELECT to_regclass('public.words')")
        if cur.fetchone()[0]:
            cur.execute("SELECT COUNT(*) FROM words")
            words_count = cur.fetchone()[0]
            
        cur.close()
        conn.close()
        
        return jsonify({
            "recordings": recordings_count,
            "words": words_count
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@audio_bp.route('/cleanup', methods=['POST'])
def cleanup_old_recordings():
    """Удалить старые записи (старше N дней)"""
    try:
        days = request.args.get('days', 30, type=int)
        cutoff_date = datetime.now() - timedelta(days=days)
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Находим старые записи
        cur.execute("SELECT filename FROM recordings WHERE created_at < %s", (cutoff_date,))
        rows = cur.fetchall()
        filenames = [r[0] for r in rows]
        
        deleted_count = 0
        s3 = get_s3_client() if (S3_BUCKET and boto3) else None
        
        for filename in filenames:
            # Удаляем из S3
            if s3:
                try:
                    s3.delete_object(Bucket=S3_BUCKET, Key=filename)
                except:
                    pass
            
            # Удаляем локально
            local_path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.exists(local_path):
                os.remove(local_path)
                
            deleted_count += 1

        # Удаляем из БД
        if filenames:
            cur.execute("DELETE FROM recordings WHERE filename = ANY(%s)", (filenames,))
            conn.commit()
            
        cur.close()
        conn.close()
        
        return jsonify({"status": "ok", "deleted": deleted_count, "days": days}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
