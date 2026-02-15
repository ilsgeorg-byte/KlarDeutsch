#!/bin/bash
# KlarDeutsch - Скрипт для быстрого запуска (Linux/Mac)

echo "========================================"
echo "KlarDeutsch Quick Start"
echo "========================================"
echo ""

# Проверка Node.js
if ! command -v node &> /dev/null; then
    echo "[ERROR] Node.js не установлен!"
    echo "Скачайте с https://nodejs.org/"
    exit 1
fi

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python не установлен!"
    echo "Скачайте с https://python.org/"
    exit 1
fi

# Проверка PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "[WARN] PostgreSQL не найден в PATH"
    echo "Убедитесь, что PostgreSQL запущен!"
fi

echo "[1/5] Установка зависимостей фронтенда..."
if [ ! -d "node_modules" ]; then
    npm install
    if [ $? -ne 0 ]; then
        echo "[ERROR] npm install не удался!"
        exit 1
    fi
fi

echo "[2/5] Установка зависимостей бэкенда..."
if [ ! -d "api/venv" ]; then
    python3 -m venv api/venv
fi
source api/venv/bin/activate
pip install -q -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[ERROR] pip install не удался!"
    exit 1
fi

echo "[3/5] Проверка база данных..."
python3 api/db.py
if [ $? -ne 0 ]; then
    echo "[WARN] Ошибка инициализации БД. Проверьте POSTGRES_URL в .env.local"
fi

echo "[4/5] Семена БД словами..."
python3 api/seed.py

echo ""
echo "========================================"
echo "Запуск серверов..."
echo "========================================"
echo ""
echo "Flask: http://127.0.0.1:5000"
echo "Next.js: http://localhost:3000"
echo ""
echo "Откройте 2 терминала и запустите:"
echo "  Терминал 1: cd api && python app.py"
echo "  Терминал 2: npm run dev"
echo ""
echo "Нажмите любую клавишу для завершения..."
read -p ""
