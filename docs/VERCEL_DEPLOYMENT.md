# Развёртывание KlarDeutsch на Vercel

## 📋 Чеклист

### 1. Подготовка

- [ ] Аккаунт на [Vercel](https://vercel.com)
- [ ] Репозиторий на GitHub
- [ ] PostgreSQL база данных (Neon, Supabase, Railway)
- [ ] Flask API развёрнут (Railway, Render, Heroku)

### 2. Vercel Project

1. **Импортируйте проект:**
   - Vercel Dashboard → Add New → Import Git Repository
   - Выберите ваш репозиторий KlarDeutsch

2. **Настройте Environment Variables:**

```
# Database
POSTGRES_URL=postgresql://user:password@host:port/database

# Security
JWT_SECRET=your-super-secret-jwt-key-min-32-chars!

# Admin Panel
ADMIN_EMAILS=your-email@example.com
ADMIN_API_TOKEN=any-secret-token-here

# API
NEXT_PUBLIC_API_URL=https://your-flask-api.com

# Site
NEXT_PUBLIC_SITE_URL=https://your-project.vercel.app
```

3. **Deploy:**
   - Нажмите "Deploy"
   - Дождитесь сборки (~2-3 мин)

### 3. Проверка

- [ ] Главная страница открывается
- [ ] Регистрация работает
- [ ] Вход работает
- [ ] Админка доступна по `/admin`

### 4. Домен (опционально)

Vercel → Settings → Domains → Add Domain

```
klardeutsch.com
www.klardeutsch.com
```

### 5. Автоматические деплои

При каждом push в `main` ветку:
- Vercel автоматически собирает проект
- Деплоит изменения через 1-2 минуты

---

## 🔧 Troubleshooting

### Ошибка сборки

```bash
# Проверьте локально
npm run build

# Если ошибка TypeScript
npm run lint
```

### Middleware не работает

- Проверьте `ADMIN_EMAILS` (точно совпадает с email)
- Очистите cookies браузера
- Проверьте JWT_SECRET (должен совпадать с Flask)

### API не отвечает

- Проверьте `NEXT_PUBLIC_API_URL`
- Убедитесь что Flask API доступен из интернета
- Проверьте CORS настройки Flask

---

## 📊 Production Checklist

- [ ] Все environment variables установлены
- [ ] PostgreSQL подключён
- [ ] Flask API работает
- [ ] Admin доступ настроен
- [ ] HTTPS включён (автоматически на Vercel)
- [ ] Домен подключён (опционально)

---

**Готово!** 🎉

Ваш сайт доступен по `https://your-project.vercel.app`  
Админка по `https://your-project.vercel.app/admin`
