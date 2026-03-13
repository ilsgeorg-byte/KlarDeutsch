# Отладка админ-панели на Vercel

## 🔍 Проблема: "Ошибка сервера" при входе

### Шаг 1: Проверьте логи на Vercel

1. Откройте https://vercel.com/dashboard
2. Ваш проект `klar-deutsch`
3. **Deployments** → Последний деплой → **View Build Logs**
4. Или **Functions** → Выберите функцию → **View Function Logs**

Ищите ошибки с:
- `Admin login error`
- `Flask API error`
- `email not in ADMIN_EMAILS`

---

### Шаг 2: Проверьте Environment Variables

Vercel → Settings → Environment Variables

**Должны быть установлены:**

```env
✅ POSTGRES_URL=postgresql://...
✅ JWT_SECRET=klardeutsch-super-secret-key-change-in-production!
✅ ADMIN_EMAILS=ваш-email@gmail.com
✅ ADMIN_API_TOKEN=any-token
✅ NEXT_PUBLIC_API_URL=https://klar-deutsch.vercel.app
```

**Как проверить:**

1. **JWT_SECRET** — должен совпадать с тем что во Flask API
2. **ADMIN_EMAILS** — точно такой же email как при входе
3. **NEXT_PUBLIC_API_URL** — URL вашего Flask API на Vercel

---

### Шаг 3: Проверьте какой JWT_SECRET используется

**Во Flask API (api/routes/auth.py):**

```python
SECRET_KEY = os.environ.get("JWT_SECRET", "klardeutsch-super-secret-key-change-in-production!")
```

**Значение по умолчанию:**
```
klardeutsch-super-secret-key-change-in-production!
```

**Если не меняли — используйте это значение на Vercel:**

```env
JWT_SECRET=klardeutsch-super-secret-key-change-in-production!
```

---

### Шаг 4: Проверьте NEXT_PUBLIC_API_URL

Поскольку Flask API тоже на Vercel, используйте:

```env
NEXT_PUBLIC_API_URL=https://klar-deutsch.vercel.app
```

**Или ваш домен если используете:**
```
NEXT_PUBLIC_API_URL=https://api.klardeutsch.com
```

---

### Шаг 5: Redeploy

После добавления переменных:

1. Vercel → Deployments
2. Нажмите **...** на последнем деплое → **Redeploy**
3. Или сделайте push в GitHub

---

## 🧪 Тестирование локально

### Запустите локально с теми же переменными:

```bash
# .env.local
POSTGRES_URL=postgresql://...
JWT_SECRET=klardeutsch-super-secret-key-change-in-production!
ADMIN_EMAILS=ваш-email@gmail.com
NEXT_PUBLIC_API_URL=https://klar-deutsch.vercel.app

# Запуск
npm run dev
```

### Попробуйте войти:

```
http://localhost:3000/admin/login
```

**Если работает локально, но не на Vercel:**
- ❌ Проблема с Environment Variables на Vercel
- ❌ Проверьте логи на Vercel

---

## 📋 Чеклист проверки

### На Vercel:

- [ ] `POSTGRES_URL` установлен
- [ ] `JWT_SECRET` установлен (совпадает с Flask API)
- [ ] `ADMIN_EMAILS` содержит ваш email
- [ ] `NEXT_PUBLIC_API_URL` установлен
- [ ] Redeploy сделан после добавления переменных

### Во Flask API (на Vercel):

- [ ] `JWT_SECRET` установлен (тот же что и в Next.js)
- [ ] `POSTGRES_URL` установлен
- [ ] CORS настроен на `https://klar-deutsch.vercel.app`

---

## 🐛 Частые ошибки

### 1. "Доступ запрещён. Ваш email не в списке администраторов."

**Причина:** Email не в `ADMIN_EMAILS`

**Решение:**
```env
ADMIN_EMAILS=ваш-email@gmail.com
```

---

### 2. "Неверный email или пароль"

**Причина:** Неверный пароль или проблема с Flask API

**Проверьте:**
- Логи Flask API на Vercel
- `POSTGRES_URL` (Flask не подключается к БД)
- `JWT_SECRET` (токен не создаётся)

---

### 3. "Ошибка сервера" (общая)

**Причина:** Исключение в коде

**Проверьте:**
- Function Logs на Vercel
- `NEXT_PUBLIC_API_URL` (Flask API недоступен)
- `JWT_SECRET` (jsonwebtoken ошибка)

---

### 4. Бесконечный редирект на логин

**Причина:** Middleware не пропускает

**Проверьте:**
- Cookie `admin_token` установлена
- Email в `ADMIN_EMAILS`
- `JWT_SECRET` совпадает

---

## 🔧 Быстрое исправление

### 1. Добавьте все переменные на Vercel:

```env
POSTGRES_URL=postgresql://...
JWT_SECRET=klardeutsch-super-secret-key-change-in-production!
ADMIN_EMAILS=ваш-email@gmail.com
ADMIN_API_TOKEN=my-admin-token-12345
NEXT_PUBLIC_API_URL=https://klar-deutsch.vercel.app
REDIS_ENABLED=false
```

### 2. Redeploy:

```bash
git add .
git commit -m "Fix admin panel env vars"
git push
```

### 3. Проверьте логи:

Vercel → Deployments → View Build Logs

---

## 📊 Логи для отладки

Теперь в логах будут детальные сообщения:

```
Admin login attempt: { email: "user@example.com", adminEmails: ["user@example.com"] }
Calling Flask API: https://klar-deutsch.vercel.app/api/auth/login
Flask API response status: 200
Flask API success: { userId: 1, email: "user@example.com" }
Admin login successful: user@example.com
```

Или ошибки:

```
Admin login error: FetchError: request to http://localhost:5000/api/auth/login failed
```

---

**После деплоя проверьте логи на Vercel и скажите что видите!**
