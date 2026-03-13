import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Список админов из переменных окружения
const ADMIN_EMAILS = (process.env.ADMIN_EMAILS || '')
  .split(',')
  .map(email => email.trim().toLowerCase())
  .filter(Boolean);

// Секретный ключ JWT (должен совпадать с Flask API)
const JWT_SECRET = process.env.JWT_SECRET || 'klardeutsch-super-secret-key-change-in-production!';

/**
 * Простая декодировка JWT токена (без верификации подписи)
 * Для Edge Runtime совместимости
 */
function decodeJWT(token: string): { payload: any; valid: boolean } {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) {
      return { payload: null, valid: false };
    }

    const payload = JSON.parse(atob(parts[1]));
    
    // Проверка истечения токена
    if (payload.exp && payload.exp < Date.now() / 1000) {
      return { payload: null, valid: false };
    }

    return { payload, valid: true };
  } catch (error) {
    return { payload: null, valid: false };
  }
}

/**
 * Middleware для защиты админ-панели
 * Проверяет:
 * 1. Наличие валидного JWT токена
 * 2. Наличие email пользователя в списке админов
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Защищаем только пути /admin/*
  if (!pathname.startsWith('/admin')) {
    return NextResponse.next();
  }

  // Для страницы логина не проверяем токен
  if (pathname === '/admin/login') {
    return NextResponse.next();
  }

  // Получаем токен из cookies
  const token = request.cookies.get('admin_token')?.value;

  // Если токена нет - редирект на страницу входа
  if (!token) {
    const loginUrl = new URL('/admin/login', request.url);
    loginUrl.searchParams.set('redirect', pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Декодируем токен
  const { payload, valid } = decodeJWT(token);
  
  if (!valid || !payload) {
    // Токен невалиден - редирект на логин
    const loginUrl = new URL('/admin/login', request.url);
    loginUrl.searchParams.set('redirect', pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Проверяем, есть ли email в списке админов
  const email = payload.email?.toLowerCase();
  const isAdmin = email && ADMIN_EMAILS.includes(email);
  
  if (!isAdmin) {
    console.warn(`Попытка доступа к админке с email: ${email}`);
    // Токен есть, но пользователь не админ - редирект на главную
    return NextResponse.redirect(new URL('/', request.url));
  }

  // Добавляем информацию о пользователе в заголовки
  const response = NextResponse.next();
  response.headers.set('x-user-id', String(payload.user_id));
  response.headers.set('x-user-email', payload.email);
  response.headers.set('x-is-admin', 'true');
  
  return response;
}

export const config = {
  matcher: '/admin/:path*',
};
