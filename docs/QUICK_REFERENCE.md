# ⚡ KlarDeutsch - Quick Reference (Быстрая справка)

## 🚀 Быстрый старт (2 минуты)

```bash
# Windows:
start.bat

# Linux/Mac:
chmod +x start.sh && ./start.sh
```

Затем в двух терминалах:
```
Терминал 1: cd api && python app.py
Терминал 2: npm run dev
```

Откройте: **http://localhost:3000**

---

## 📁 Где что находится?

| Что | Где | Зачем |
|-----|-----|-------|
| Слова | `api/data_words.py` | Словарь на A1, A2, B1 |
| API слова | `api/routes/words.py` | GET /api/words |
| API аудио | `api/routes/audio.py` | POST /api/audio |
| Главная | `app/page.tsx` | http://localhost:3000 |
| Тренажер | `app/trainer/page.tsx` | http://localhost:3000/trainer |
| Записи | `app/audio/page.tsx` | http://localhost:3000/audio |
| Стили | `app/styles/Shared.module.css` | Общие стили |
| Ошибки | `app/components/ErrorBoundary.tsx` | Ловля ошибок |

---

## 🔧 Конфигурация

### .env.local (скопировать из .env.local.example)

```ini
# PostgreSQL URL
POSTGRES_URL=postgresql://postgres:password@localhost:5432/klardeutsch

# Опционально:
UPLOAD_DIR=./api/uploads
FLASK_ENV=development
```

### requirements.txt

```
Flask==3.0.0
flask-cors==4.0.0
psycopg2-binary==2.9.9
python-dotenv==1.0.0
```

---

## 📍 API Endpoints

```
GET    /api/words                    # Все слова (с параметрами)
  ?level=A1&skip=0&limit=100

GET    /api/words/<id>               # Одно слово по ID

GET    /api/words/by-topic/Семья    # Слова по теме

GET    /api/levels                   # [A1, A2, B1, B2, C1]

GET    /api/topics?level=A1         # Темы уровня

POST   /api/audio                    # Загрузить аудио
       Content-Type: multipart/form-data
       file: <webm/mp3>

GET    /api/list_audio              # Список файлов

POST   /api/delete_audio            # Удалить файл
       {"filename": "..."}

GET    /api/files/<filename>        # Скачать аудио

GET    /health                       # Статус сервера
```

---

## 🧪 Тестирование

### Curl
```bash
# Слова
curl http://127.0.0.1:5000/api/words?level=A1

# Уровни
curl http://127.0.0.1:5000/api/levels

# Здоровье
curl http://127.0.0.1:5000/health
```

### Python
```python
import requests

# Получить слова
r = requests.get('http://127.0.0.1:5000/api/words?level=A1')
print(r.json())

# Загрузить файл
with open('audio.webm', 'rb') as f:
    files = {'file': f}
    r = requests.post('http://127.0.0.1:5000/api/audio', files=files)
    print(r.json())
```

---

## 🛠️ Обслуживание

### Добавить новое слово

1. Отредактируйте `api/data_words.py`
2. Запустите `python api/seed.py`

Формат:
```python
{
    "level": "A1",  # A1, A2, B1, B2, C1
    "topic": "Семья",
    "de": "Mutter",
    "ru": "Мать",
    "article": "die",  # der, die, das, или ""
    "example_de": "Das ist meine Mutter",
    "example_ru": "Это моя мать"
}
```

### Очистить БД и пересеять

```bash
cd api
psql -U postgres -d klardeutsch -c "TRUNCATE words CASCADE;"
python seed.py
```

### Backup БД

```bash
pg_dump -U postgres klardeutsch > backup.sql
```

### Restore БД

```bash
psql -U postgres -d klardeutsch < backup.sql
```

---

## 🐛 Debug

### Включить детальное логирование

В `api/index.py`:
```python
app.run(debug=True, port=5000)
```

В браузере нажмите F12 → Console для ошибок JS.

### Проверка конфигурации

```bash
python check_setup.py
```

---

## 📚 Документация

| Документ | Что | Для кого |
|----------|-----|----------|
| [README_IMPROVEMENTS.md](README_IMPROVEMENTS.md) | Полное руководство (680 строк) | Разработчики |
| [FIRST_RUN.md](FIRST_RUN.md) | Инструкция первого запуска | Новички |
| [CHANGES_SUMMARY.md](CHANGES_SUMMARY.md) | Что изменилось | Код ревью |
| [FILES_MANIFEST.md](FILES_MANIFEST.md) | Список всех файлов | Для навигации |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | Эта справка | Быстрый доступ |

---

## ⚠️ Распространённые ошибки

| Ошибка | Решение |
|--------|---------|
| `ModuleNotFoundError: routes` | Проверьте `api/routes/__init__.py` существует |
| `CORS error` | Flask не запущен или на другом порту |
| `psycopg2.OperationalError` | Проверьте POSTGRES_URL, запустите PostgreSQL |
| `Port already in use` | Измените порт в `api/app.py` или `next.config.mjs` |
| `Module not found: next.config` | `rm -rf .next && npm run dev` |

---

## 🚀 Production Deploy

### Frontend (Vercel)

1. `git push origin main`
2. Vercel автоматически задеплойится
3. Установите `NEXT_PUBLIC_API_URL` в env vars

### Backend (Railway)

```bash
railway init
railway up
```

---

## 📊 Структура папок

```
api/                    Backend
├── routes/            Маршруты (blueprints)
│   ├── words.py      GET/слова
│   └── audio.py      POST/аудио
├── data_words.py      База слов
├── index.py          Главное приложение
└── uploads/          Аудиофайлы

app/                   Frontend
├── components/       Компоненты
│   └── ErrorBoundary React error handling
├── styles/          Стили
│   └── Shared.module.css
├── trainer/         Страница тренажера
├── audio/           Страница записей
├── page.tsx         Главная
└── layout.tsx       Layout с ErrorBoundary
```

---

## 🎯 Следующие шаги

1. ✅ Протестировать локально (check_setup.py)
2. ✅ Запустить (start.bat или start.sh)
3.📝 Добавить новые слова в data_words.py
4. 🔐 Добавить валидацию пользователя (auth)
5. 💾 Сохранять прогресс пользователя
6. 🔊 Проверка произношения (Web Speech API)
7. 📱 Mobile версия (React Native)
8. 🧪 Unit тесты (pytest + Jest)

---

## 🆘 Help Commands

```bash
# Диагностика
python check_setup.py

# Быстрый запуск
./start.sh              # Linux/Mac
start.bat               # Windows

# Установать зависимости
npm install
pip install -r requirements.txt

# Запустить БД скрипты
python api/db.py       # Создать таблицы
python api/seed.py     # Добавить слова

# Запустить серверы
cd api && python app.py     # Flask http://127.0.0.1:5000
npm run dev                 # Next.js http://localhost:3000
```

---

## 📞 Контакты ошибок

Если не работает:
1. Запустите `python check_setup.py`
2. Прочитайте [FIRST_RUN.md](FIRST_RUN.md)
3. Проверьте терминалы на ошибки
4. Посмотрите раздел "Распространённые ошибки"

---

**Версия:** 1.0.0  
**Дата:** 15 февраля 2026  
**Статус:** ✅ Готово к использованию

