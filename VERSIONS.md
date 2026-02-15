# KlarDeutsch - Версии и зависимости

## 📦 Версии пакетов

### Frontend (Node.js)

```json
{
  "dependencies": {
    "lucide-react": "^0.564.0",
    "next": "14.1.0",
    "react": "18.2.0",
    "react-dom": "18.2.0"
  },
  "devDependencies": {
    "@types/node": "20.10.0",
    "@types/react": "18.2.37",
    "@types/react-dom": "18.2.15",
    "autoprefixer": "^10.4.24",
    "eslint": "8.55.0",
    "eslint-config-next": "14.1.0",
    "postcss": "^8.5.6",
    "tailwindcss": "3.4",
    "typescript": "5.3.3"
  }
}
```

**Node.js требует:** >= 16.8.0  
**npm требует:** >= 7.0.0

### Backend (Python)

```
Flask==3.0.0
flask-cors==4.0.0
psycopg2-binary==2.9.9
python-dotenv==1.0.0
python-decouple==3.8
```

**Python требует:** >= 3.8

---

## 🐘 PostgreSQL

**Требуемая версия:** >= 12.0

**Установка:**

- **Windows:** https://www.postgresql.org/download/windows/
- **Mac:** `brew install postgresql`
- **Linux:** `sudo apt-get install postgresql postgresql-contrib`

**Создание БД:**

```bash
createdb -U postgres klardeutsch

# Или через psql:
psql -U postgres
CREATE DATABASE klardeutsch;
```

---

## 🔍 Проверка версий

```bash
# Node.js и npm
node --version    # должен быть >= 16.8.0
npm --version     # должен быть >= 7.0.0

# Python
python --version  # должен быть >= 3.8

# PostgreSQL
psql --version    # должен быть >= 12.0

# Git (опционально)
git --version
```

---

## 🔄 Обновление пакетов

### Frontend

```bash
npm update              # Обновить все
npm update next react   # Обновить конкретные
npm outdated           # Показать устаревшие
```

### Backend

```bash
pip install --upgrade pip
pip list --outdated
pip install -U -r requirements.txt
```

---

## ⚠️ Совместимость

| Компонент | Версия | Статус |
|-----------|--------|--------|
| Node.js | 16+ | ✅ Проверено |
| npm | 7+ | ✅ Проверено |
| Python | 3.8+ | ✅ Проверено |
| PostgreSQL | 12+ | ✅ Проверено |
| Flask | 3.0.0 | ✅ Проверено |
| Next.js | 14.1.0 | ✅ Проверено |
| React | 18.2.0 | ✅ Проверено |
| TypeScript | 5.3.3 | ✅ Проверено |

---

## 🐛 Известные проблемы

### Flask 3.0.0 + Werkzeug

Если видите ошибку про `werkzeug`, обновите pip:
```bash
pip install --upgrade pip
```

### Node.js на M1/M2 Mac

Используйте x64 версию Node.js:
```bash
brew install node@18
```

### PostgreSQL на Windows

Используйте абсолютный путь в POSTGRES_URL:
```ini
POSTGRES_URL=postgresql://postgres:password@localhost:5432/klardeutsch
```

---

## 📝 Лицензии зависимостей

| Пакет | Лицензия |
|-------|----------|
| Flask | BSD-3-Clause |
| flask-cors | MIT |
| psycopg2 | LGPL |
| python-dotenv | BSD-3-Clause |
| Next.js | MIT |
| React | MIT |
| Tailwind CSS | MIT |
| TypeScript | Apache-2.0 |

---

## 🔐 Безопасность

### Security Updates

Проверяйте обновления:

```bash
# Frontend
npm audit

# Backend
pip check
```

Исправляйте уязвимости:

```bash
npm audit fix
```

---

## 📊 Версиозависимости обновлены

**Дата последнего обновления:** 15 февраля 2026

**Обновленные пакеты:**
- ✅ Flask (2.x → 3.0.0)
- ✅ flask-cors (стабильная версия)
- ✅ требуется указание у всех пакетов

---

Для установки используйте:

```bash
pip install -r requirements.txt
npm install
```

