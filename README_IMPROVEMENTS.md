# KlarDeutsch - Полное руководство по запуску

## 📋 Структура проекта (после обновления)

```
KlarDeutsch/
├── app/                          # Next.js фронтенд
│   ├── components/
│   │   └── ErrorBoundary.tsx    # Обработка ошибок
│   ├── styles/
│   │   └── Shared.module.css    # Общие стили (НОВОЕ)
│   ├── trainer/
│   │   └── page.tsx
│   ├── audio/
│   │   └── page.tsx
│   ├── layout.tsx               # С Error Boundary (ОБНОВЛЕНО)
│   ├── page.tsx                 # Главная страница
│   └── globals.css
│
├── api/                          # Flask бэкенд
│   ├── routes/                  # Организованные маршруты (НОВОЕ)
│   │   ├── words.py            # API для слов
│   │   ├── audio.py            # API для аудио с валидацией
│   │   └── __init__.py
│   ├── data_words.py           # База данных слов (НОВОЕ)
│   ├── db.py                   # Подключение к БД
│   ├── index.py                # Основное приложение (РЕФАКТОРЕНО)
│   ├── uploads/                # Директория для аудиозаписей
│   └── __pycache__/
│
├── package.json
├── requirements.txt           # ОБНОВЛЕНО (версии пакетов)
├── next.config.mjs           # ОБНОВЛЕНО (правильные rewrites)
├── tsconfig.json
├── postcss.config.js
├── tailwind.config.js
├── .env.local                 # Ваши POSTGRES_URL и т.д.
└── README_IMPROVEMENTS.md     # Этот файл
```

---

## 🚀 Локальный запуск (разработка)

### 1. Подготовка окружения

```bash
# Перейдите в корневую папку проекта
cd c:\Users\george\Documents\KlarDeutsch

# Убедитесь, что есть файл .env.local с переменными:
# POSTGRES_URL=postgresql://user:password@localhost:5432/klardeutsch
# UPLOAD_DIR=/path/to/uploads (опционально)
```

### 2. Установка зависимостей фронтенда

```bash
npm install
```

### 3. Установка зависимостей бэкенда

```bash
cd api
pip install -r ../requirements.txt
```

### 4. Инициализация БД (первый запуск)

```bash
# Создание таблиц
python db.py

# Добавление слов в БД
python seed.py
```

### 5. Запуск в двух терминалах

**Терминал 1 - Flask сервер:**
```bash
cd api
python app.py
# Flask будет на http://127.0.0.1:5000
```

**Терминал 2 - Next.js сервер:**
```bash
npm run dev
# Next.js будет на http://localhost:3000
```

Откройте браузер: **http://localhost:3000**

---

## 🔧 Что изменилось

### ✨ Улучшения бэкенда

1. **Структура маршрутов (routes/)**
   - `routes/words.py` - все API для слов
   - `routes/audio.py` - все API для аудио
   - Легче поддерживать и расширять

2. **Валидация и безопасность**
   - Проверка расширения файлов (только webm, mp3, wav, ogg)
   - Проверка размера файла (макс 5MB)
   - Защита от path traversal атак
   - Параметризованные SQL запросы (защита от SQL injection)

3. **Новые API endpoints:**
   - `GET /api/words?level=A1&skip=0&limit=100` - пагинация
   - `GET /api/words/<id>` - одно слово по ID
   - `GET /api/words/by-topic/<topic>` - слова по теме
   - `GET /api/levels` - список уровней
   - `GET /api/topics?level=A1` - темы по уровню
   - `GET /health` - проверка статуса сервера

4. **Error handling**
   - Правильные HTTP коды (404, 400, 500)
   - Четкие сообщения об ошибках
   - Логирование запросов (в режиме разработки)

### ✨ Улучшения фронтенда

1. **Error Boundary**
   - Ловле ошибок во всех компонентах
   - Красивая страница ошибки
   - Кнопка для повторной попытки
   - Детали ошибки в режиме разработки

2. **Общие стили**
   - CSS модуль перемещен в `app/styles/`
   - Используется всеми страницами (домой, тренажер, аудио)
   - Как результат проще обновлять дизайн

3. **Лучшая конфигурация Next.js**
   - Правильные rewrites для API
   - Поддержка файлов

---

## 📦 Требуемые пакеты

**Frontend (package.json):**
- next 14.1.0
- react 18.2.0
- react-dom 18.2.0
- tailwindcss 3.4
- lucide-react (иконки)

**Backend (requirements.txt):**
- Flask 3.0.0
- flask-cors 4.0.0
- psycopg2-binary 2.9.9
- python-dotenv 1.0.0

---

## 🚀 Деплой на Vercel (фронтенд)

### 1. Подготовка к деплою

```bash
# Убедитесь, что проект в git репозитории
git add .
git commit -m "Refactor: improve project structure and security"
git push origin main
```

### 2. На сайте Vercel (vercel.com)

1. Создайте новый проект (Import from Git)
2. Выберите ваш GitHub репозиторий
3. В Settings → Environment Variables добавьте:
   ```
   NEXT_PUBLIC_API_URL=https://your-api-domain.com
   ```

4. Deploy!

### 3. Бэкенд Flask (отдельно)

Так как Vercel не поддерживает Python-бэкенды нативно, используйте:

**Вариант 1 - Railway.app** (рекомендуется)
```bash
# Установите railways CLI
# https://docs.railway.app/getting-started

railway init  # Выберите существующий проект или создайте новый
railway up    # Задеплойте

# Railway установит переменные окружения автоматически
```

**Вариант 2 - Render.com**
```bash
# Создайте новый Web Service
# GitHub repo → Select Branch → Build command
# Тип: Python 3
# Start command: python api/app.py
```

**Вариант 3 - PythonAnywhere.com**
- Простой хостинг для Flask приложений
- Есть бесплатный тариф

---

## 🧪 Тестирование API

### Используя curl:

```bash
# Получить слова уровня A1
curl http://127.0.0.1:5000/api/words?level=A1

# Получить темы
curl http://127.0.0.1:5000/api/topics?level=A1

# Загрузить аудио
curl -X POST -F "file=@recording.webm" http://127.0.0.1:5000/api/audio

# Проверить здоровье сервера
curl http://127.0.0.1:5000/health
```

### Используя Python:

```python
import requests

# Получить слова
response = requests.get('http://127.0.0.1:5000/api/words', params={'level': 'A1'})
print(response.json())

# Загрузить файл
with open('recording.webm', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://127.0.0.1:5000/api/audio', files=files)
    print(response.json())
```

---

## 📝 Миграция существующих данных

Если у вас уже есть данные в БД:

```bash
# Резервная копия
pg_dump -U user database_name > backup.sql

# Если нужно перезаписать:
psql -U user database_name < backup.sql
```

---

## 🔐 Safety Checklist перед production

- [ ] CORS настроен на конкретные домены (не '*')
- [ ] UPLOAD_DIR указывает на постоянное хранилище
- [ ] Дополнительная валидация для пользовательского ввода
- [ ] Rate limiting добавлен (можно flask-limiter)
- [ ] HTTPS включен на сервере
- [ ] Логи записываются в файл
- [ ] Backup БД настроен
- [ ] Переменные окружения не коммитятся (.env.local в .gitignore)

---

## 🛡️ Улучшения безопасности (новое)
- Добавлены функции санитизации ввода данных поверх Pydantic схем
- Создан модуль `api/utils/sanitization_utils.py` с функциями для очистки строк, валидации email, имен пользователей и т.д.
- Обновлены все Pydantic схемы в `api/schemas.py` для использования новых валидаторов
- Добавлена документация по санитизации в `api/SANITIZATION_GUIDELINES.md`

## 📊 Возможные улучшения на будущее

1. **Authentication** - добавить логин/регистрацию
2. **User progress** - сохранять прогресс пользователя
3. **Pronunciation check** - использовать Web Speech API для проверки произношения
4. **Admin panel** - управление словами
5. **Offline mode** - кеширование слов локально
6. **Mobile app** - React Native версия
7. **Tests** - pytest для бэкенда, Jest для фронтенда
8. **CI/CD** - GitHub Actions для автоматического тестирования и деплоя

---

## 🐛 Troubleshooting

**Ошибка "ModuleNotFoundError: No module named 'routes'"**
- Убедитесь, что в папке `api/routes/` есть файл `__init__.py`

**CORS ошибка при загрузке аудио**
- Проверьте что Flask запущен на `http://127.0.0.1:5000`
- Проверьте Origin в браузере (Console → Network)

**БД не подключается**
- Проверьте переменную `POSTGRES_URL` в `.env.local`
- Убедитесь, что PostgreSQL запущен
- Проверьте права доступа

**Файлы не сохраняются после перезагрузки**
- Используйте постоянное хранилище (не `/tmp`)
- Установите `UPLOAD_DIR` переменную окружения

---

Все готово к использованию! 🎉

