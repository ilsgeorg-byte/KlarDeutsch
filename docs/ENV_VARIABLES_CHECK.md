# Проверка Environment Variables на Vercel

## ✅ Уже есть:
- [x] `POSTGRES_URL` — Подключение к базе данных

## ❓ Нужно проверить/добавить:

### 1. JWT_SECRET
**Где проверить во Flask API:**

Откройте файл `api/app.py` или `api/routes/auth.py` и найдите:

```python
SECRET_KEY = os.environ.get("JWT_SECRET", "klardeutsch-super-secret-key-change-in-production!")
```

**Варианты:**

**A. Если используете значение по умолчанию:**
```env
JWT_SECRET=klardeutsch-super-secret-key-change-in-production!
```

**B. Если хотите свой (рекомендуется для production):**

Сгенерируйте новый:
```bash
# PowerShell (Windows):
[System.Web.Security.Membership]::GeneratePassword(32, 8)

# Или онлайн: https://generate-secret.vercel.app/32
```

**Добавьте на Vercel:**
```
JWT_SECRET=your-generated-secret-here
```

**И обновите во Flask API** (на Railway/Render):
```env
JWT_SECRET=your-generated-secret-here
```

⚠️ **Важно:** `JWT_SECRET` должен **одинаковым** быть и в Next.js (Vercel), и во Flask API!

---

### 2. ADMIN_EMAILS

**Добавьте на Vercel:**

```env
ADMIN_EMAILS=ваш-email@gmail.com
```

**Где используется:**
- Доступ к `/admin` панели
- Только эти email могут войти в админку

**Как проверить:**
1. Зарегистрируйтесь на сайте через `/register`
2. Используйте тот же email что указали в `ADMIN_EMAILS`
3. Войдите через `/admin/login`

---

### 3. ADMIN_API_TOKEN

**Добавьте на Vercel:**

```env
ADMIN_API_TOKEN=any-secret-token-min-32-chars
```

**Где используется:**
- Внутренние API запросы Next.js → Flask
- Будет нужен для Flask API endpoints

**Для Flask API (Railway/Render) добавьте такую же переменную:**
```env
ADMIN_API_TOKEN=any-secret-token-min-32-chars
```

---

### 4. REDIS_ENABLED

**Для начала отключите Redis:**

```env
REDIS_ENABLED=false
```

Позже можно подключить Upstash Redis для кэширования.

---

### 5. NEXT_PUBLIC_API_URL

**Где взять URL Flask API:**

**Railway:**
1. https://railway.app/dashboard
2. Ваш проект → Settings → Networking
3. Public URL: `https://your-project.railway.app`

**Render:**
1. https://render.com/dashboard
2. Ваш сервис → URL: `https://your-service.onrender.com`

**Heroku:**
1. https://dashboard.heroku.com/apps
2. Ваш app → Settings → Domains
3. `https://your-app.herokuapp.com`

**Добавьте на Vercel:**
```env
NEXT_PUBLIC_API_URL=https://your-flask-api.railway.app
```

---

### 6. NEXT_PUBLIC_SITE_URL

**Для Vercel:**

```env
NEXT_PUBLIC_SITE_URL=https://klar-deutsch.vercel.app
```

**Если используете свой домен:**
```env
NEXT_PUBLIC_SITE_URL=https://klardeutsch.com
```

---

## 📋 Итоговый чеклист

### На Vercel:

```env
✅ POSTGRES_URL=postgresql://... (уже есть)
❓ JWT_SECRET=... (должен совпадать с Flask)
❓ ADMIN_EMAILS=your-email@gmail.com
❓ ADMIN_API_TOKEN=any-secret-token
❓ REDIS_ENABLED=false
❓ NEXT_PUBLIC_API_URL=https://your-flask-api.com
❓ NEXT_PUBLIC_SITE_URL=https://klar-deutsch.vercel.app
```

### На Flask API (Railway/Render/Heroku):

```env
✅ POSTGRES_URL=postgresql://... (уже есть)
❓ JWT_SECRET=... (такое же как на Vercel!)
❓ ADMIN_API_TOKEN=... (такое же как на Vercel!)
```

---

## 🔧 Как добавить переменные на Vercel

1. https://vercel.com/dashboard
2. Ваш проект → **Settings**
3. **Environment Variables**
4. **Add New** → Введите имя и значение
5. **Environment:** ✅ Production, ✅ Preview, ✅ Development
6. **Save**
7. **Redeploy** (чтобы применилось)

---

## 🧪 Проверка после настройки

### 1. Главная страница
```
https://klar-deutsch.vercel.app
```
✅ Открывается без ошибок

### 2. Регистрация
```
https://klar-deutsch.vercel.app/register
```
✅ Работает, пользователь создаётся в БД

### 3. Вход
```
https://klar-deutsch.vercel.app/login
```
✅ Токен сохраняется в cookies

### 4. Админка
```
https://klar-deutsch.vercel.app/admin
```
✅ Если email в `ADMIN_EMAILS` — пускает
✅ Если нет — редирект на `/admin/login`

---

## ⚠️ Если JWT_SECRET не совпадает

**Симптомы:**
- Вход работает, но админка не пускает
- Ошибка "Токен невалиден"
- Бесконечный редирект на логин

**Решение:**
1. Проверьте `JWT_SECRET` на Vercel
2. Проверьте `JWT_SECRET` на Flask API (Railway/Render)
3. Убедитесь что они **одинаковые**
4. Redeploy обоих проектов

---

## 📊 Сводная таблица

| Переменная | Vercel (Next.js) | Flask API (Railway) | Критично |
|------------|------------------|---------------------|----------|
| POSTGRES_URL | ✅ Уже есть | ✅ Уже есть | ✅ Да |
| JWT_SECRET | ❓ Нужно | ❓ Нужно | ✅ Да (должно совпадать!) |
| ADMIN_EMAILS | ❓ Нужно | ❌ Не нужно | ✅ Да |
| ADMIN_API_TOKEN | ❓ Нужно | ❓ Нужно | ⚠️ Для API |
| REDIS_ENABLED | ❓ Нужно | ❌ Не нужно | ❌ Нет |
| NEXT_PUBLIC_API_URL | ❓ Нужно | ❌ Не нужно | ✅ Да |
| NEXT_PUBLIC_SITE_URL | ❓ Нужно | ❌ Не нужно | ⚠️ Для metadata |

---

**Следующий шаг:** Проверьте `JWT_SECRET` во Flask API и добавьте остальные переменные на Vercel.
