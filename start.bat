@echo off
REM KlarDeutsch - Скрипт для быстрого запуска (Windows)

echo ========================================
echo KlarDeutsch Quick Start
echo ========================================
echo.

REM Проверка Node.js
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js не установлен!
    echo Скачайте с https://nodejs.org/
    pause
    exit /b 1
)

REM Проверка Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python не установлен!
    echo Скачайте с https://python.org/
    pause
    exit /b 1
)

REM Проверка PostgreSQL
where psql >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [WARN] PostgreSQL не найден в PATH
    echo Убедитесь, что PostgreSQL запущен!
)

echo [1/5] Установка зависимостей фронтенда...
if not exist "node_modules" (
    call npm install
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] npm install не удался!
        pause
        exit /b 1
    )
)

echo [2/5] Установка зависимостей бэкенда...
if not exist "api\venv" (
    call python -m venv api\venv
)
call api\venv\Scripts\activate.bat
call pip install -q -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] pip install не удался!
    pause
    exit /b 1
)

echo [3/5] Проверка база данных...
python api\db.py
if %ERRORLEVEL% NEQ 0 (
    echo [WARN] Ошибка инициализации БД. Проверьте POSTGRES_URL в .env.local
)

echo [4/5] Семена БД словами...
python api\seed.py

echo.
echo ========================================
echo Запуск серверов...
echo ========================================
echo.
echo Flask: http://127.0.0.1:5000
echo Next.js: http://localhost:3000
echo.
echo Откройте 2 терминала и запустите:
echo   Терминал 1: cd api && python app.py
echo   Терминал 2: npm run dev
echo.
echo Нажмите любую клавишу...

pause
