# Панель администратора KlarDeutsch

## 📋 Обзор

Полнофункциональная панель администратора для управления контентом и пользователями KlarDeutsch.

---

## 🔐 Доступ

### Настройка

1. **Скопируйте `.env.local.example` в `.env.local`:**

```bash
cp .env.local.example .env.local
```

2. **Добавьте email админа:**

```env
ADMIN_EMAILS=admin@klardeutsch.com,your-email@example.com
```

3. **Установите ADMIN_API_TOKEN:**

```env
ADMIN_API_TOKEN=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
```

### Вход

- **URL:** `http://localhost:3000/admin`
- **Логин:** Email из `ADMIN_EMAILS`
- **Пароль:** Ваш пароль от аккаунта

---

## 🏗️ Структура

```
app/admin/
├── layout.tsx              # Layout с sidebar
├── login/page.tsx          # Страница входа
├── page.tsx                # Дашборд
├── words/page.tsx          # Управление словами
├── users/page.tsx          # Пользователи
├── diary/page.tsx          # Дневник
└── stats/page.tsx          # Статистика

app/api/admin/
├── auth/route.ts           # Авторизация
├── stats/route.ts          # Статистика API
├── words/route.ts          # Слова API
└── users/route.ts          # Пользователи API

middleware.ts               # Проверка прав доступа
```

---

## 🎯 Функционал

### Дашборд (`/admin`)

- **Статистика:**
  - Всего слов
  - Пользователей (активные сегодня)
  - Записей в дневнике
  - Процент активности

- **Слова по уровням:** Таблица с прогрессом
- **Быстрые действия:** Ссылки на разделы

### Слова (`/admin/words`)

- **Просмотр:** Список всех слов с пагинацией
- **Фильтры:**
  - Поиск по тексту
  - Фильтр по уровню (A1-C1)
- **Добавление:** Модальное окно с формой
- **Редактирование:** Изменение существующих слов
- **Удаление:** Удаление слов (TODO: API)

**Поля слова:**
- Немецкое слово
- Артикль (der/die/das)
- Русский перевод
- Уровень (A1-C1)
- Тема

### Пользователи (`/admin/users`)

- **Список:** Все пользователи с пагинацией
- **Поиск:** По email и имени
- **Блокировка:** Вкл/выкл аккаунт (TODO: API)
- **Удаление:** Удаление пользователя (TODO: API)

**Данные пользователя:**
- ID
- Имя (аватар)
- Email
- Дата регистрации
- Статус (активен/заблокирован)

### Дневник (`/admin/diary`)

- **Просмотр:** Записи дневника пользователей
- **Модерация:** Просмотр оригинала и исправлений
- **Удаление:** Удаление записей (TODO: API)

### Статистика (`/admin/stats`)

- **Периоды:** 24h, 7d, 30d, 90d
- **Графики:**
  - Активность пользователей
  - Изученные слова
- **Таблицы:**
  - Распределение по уровням
  - Мин/сред/макс значения

---

## 🔒 Безопасность

### Middleware

`middleware.ts` проверяет:

1. Наличие JWT токена в cookie
2. Валидность токена
3. Наличие email в `ADMIN_EMAILS`

### Защита

- **Cookie:** `httpOnly`, `secure` (production)
- **Токен:** Истекает через 8 часов
- **API:** Проверка токена для внутренних запросов

---

## 🎨 UI Компоненты

### Стили

Все стили в `app/admin/adminStyles.css`:

- **Sidebar:** Фиксированная боковая панель
- **Cards:** Карточки для контента
- **Tables:** Таблицы с данными
- **Forms:** Формы для ввода
- **Buttons:** Кнопки (primary, secondary, danger)
- **Badges:** Статусы (уровни, статусы)
- **Pagination:** Постраничная навигация
- **Modals:** Модальные окна

### Адаптивность

- **Desktop:** Полный sidebar
- **Tablet:** Сокращённый sidebar
- **Mobile:** Hamburger menu

---

## 📡 API Endpoints

### Авторизация

```
POST /api/admin/auth
Body: { email, password }
Response: { success, user }
```

### Статистика

```
GET /api/admin/stats
Response: {
  words: { total, by_level },
  users: { total, active_today },
  diary: { total_entries, today }
}
```

### Слова

```
GET /api/admin/words?page=1&limit=20&level=A1&search=haus
POST /api/admin/words
Body: { de, ru, article, level, topic }
```

### Пользователи

```
GET /api/admin/users?page=1&limit=20&search=email
```

---

## 🚀 Развёртывание на Vercel

### 1. Environment Variables

В панели Vercel добавьте переменные:

```env
# Обязательные
POSTGRES_URL=postgresql://user:pass@host:5432/klardeutsch
JWT_SECRET=your-super-secret-jwt-key-min-32-chars!

# Admin Panel
ADMIN_EMAILS=admin@klardeutsch.com
ADMIN_API_TOKEN=your-admin-api-token-here

# Опционально
REDIS_ENABLED=false
NEXT_PUBLIC_API_URL=https://your-flask-api.com
NEXT_PUBLIC_SITE_URL=https://klar-deutsch.vercel.app
```

### 2. Push на GitHub

```bash
git add .
git commit -m "Add admin panel"
git push
```

Vercel автоматически соберёт и развернёт проект.

### 3. Доступ к админке

- **URL:** `https://klar-deutsch.vercel.app/admin`
- **Вход:** Email из `ADMIN_EMAILS` + пароль от аккаунта

### ⚠️ Edge Runtime

Middleware использует Edge Runtime для совместимости с Vercel:
- JWT декодируется без внешних зависимостей
- Нет `jsonwebtoken` в middleware
- Полная совместимость с Vercel Edge Functions

---

## 🛠️ TODO

### API (Flask)

- [ ] `GET /api/admin/stats/words` — Статистика слов
- [ ] `GET /api/admin/stats/users` — Статистика пользователей
- [ ] `GET /api/admin/stats/diary` — Статистика дневника
- [ ] `GET /api/admin/users` — Список пользователей
- [ ] `POST /api/admin/users/:id/block` — Блокировка
- [ ] `DELETE /api/admin/users/:id` — Удаление
- [ ] `DELETE /api/admin/words/:id` — Удаление слова
- [ ] `PUT /api/admin/words/:id` — Обновление слова
- [ ] `GET /api/admin/diary` — Записи дневника
- [ ] `DELETE /api/admin/diary/:id` — Удаление записи

### Frontend

- [ ] Экспорт данных (CSV, Excel)
- [ ] Массовые операции (выбрать несколько)
- [ ] Уведомления пользователям
- [ ] Лог действий админа
- [ ] Настройки системы

---

## 🚀 Использование

### Запуск

```bash
# Development
npm run dev

# Посетите http://localhost:3000/admin
```

### Первый вход

1. Создайте аккаунт через `/register`
2. Добавьте email в `ADMIN_EMAILS`
3. Войдите через `/admin/login`

---

## 📊 Скриншоты

### Дашборд
```
┌─────────────────────────────────────────┐
│  KlarDeutsch Admin    [User] [Logout]   │
├─────────────────────────────────────────┤
│ Dashboard  │  ┌─────┐ ┌─────┐ ┌─────┐  │
│ Words      │  │Words│ │Users│ │Diary│  │
│ Users      │  │ 1234│ │ 567 │ │ 890 │  │
│ Diary      │  └─────┘ └─────┘ └─────┘  │
│ Stats      │                            │
│            │  Words by Level            │
│            │  A1: ████ 25%              │
│            │  A2: ████ 25%              │
│            │  B1: ████ 25%              │
│            │  B2: ████ 25%              │
└────────────┴────────────────────────────┘
```

---

## ⚙️ Конфигурация

### Переменные окружения

```env
# Список админов
ADMIN_EMAILS=admin@example.com,admin2@example.com

# Токен для API
ADMIN_API_TOKEN=super-secret-token

# JWT Secret (должен совпадать с Flask)
JWT_SECRET=your-jwt-secret
```

---

## 🐛 Troubleshooting

### "Доступ запрещён"

- Проверьте `ADMIN_EMAILS` в `.env.local`
- Email должен точно совпадать (case-sensitive)
- Перезапустите dev-сервер

### "Ошибка входа"

- Проверьте пароль от аккаунта
- Убедитесь, что аккаунт существует
- Проверьте Flask API (`POSTGRES_URL`, `JWT_SECRET`)

### Middleware не работает

- Очистите cookies браузера
- Проверьте `middleware.ts` в корне проекта
- Убедитесь, что Next.js видит файл

---

**Версия:** 1.0.0  
**Дата:** Март 2026  
**Статус:** ✅ Production Ready (API в разработке)
