# Используем легкий образ Python
FROM python:3.11-slim

# Установка переменных окружения для Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Рабочая директория в контейнере
WORKDIR /app

# Установка системных зависимостей (нужны для psycopg2 и др.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости из корня (так как requirements.txt там)
COPY ../requirements.txt .

# Установка Python-библиотек
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код API
COPY . .

# Папка для загрузки аудио
RUN mkdir -p uploads && chmod 777 uploads

# Открываем порт
EXPOSE 5000

# Запуск через Gunicorn (4 воркера для параллельной обработки запросов)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "index:app"]
