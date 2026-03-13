/**
 * API для админ-панели
 * Проверка токена и получение данных админа
 */

import { NextRequest, NextResponse } from 'next/server';
import jwt from 'jsonwebtoken';

const JWT_SECRET = process.env.JWT_SECRET || 'klardeutsch-super-secret-key-change-in-production!';
const ADMIN_EMAILS = (process.env.ADMIN_EMAILS || '')
  .split(',')
  .map(email => email.trim().toLowerCase())
  .filter(Boolean);

export async function POST(request: NextRequest) {
  try {
    const { email, password } = await request.json();

    if (!email || !password) {
      return NextResponse.json(
        { error: 'Email и пароль обязательны' },
        { status: 400 }
      );
    }

    // Проверяем, есть ли email в списке админов
    if (!ADMIN_EMAILS.includes(email.toLowerCase())) {
      return NextResponse.json(
        { error: 'Доступ запрещён' },
        { status: 403 }
      );
    }

    // Проверяем пароль через Flask API
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:5000';
    const loginResponse = await fetch(`${apiBaseUrl}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!loginResponse.ok) {
      const errorData = await loginResponse.json().catch(() => ({}));
      return NextResponse.json(
        { error: errorData.error || 'Неверный email или пароль' },
        { status: 401 }
      );
    }

    const { token, user } = await loginResponse.json();

    // Создаём свою cookie для админки
    const adminToken = jwt.sign(
      {
        user_id: user.id,
        email: user.email,
        username: user.username,
        is_admin: true,
      },
      JWT_SECRET,
      { expiresIn: '8h' }
    );

    const response = NextResponse.json({
      success: true,
      user: {
        id: user.id,
        email: user.email,
        username: user.username,
      },
    });

    response.cookies.set('admin_token', adminToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 60 * 60 * 8, // 8 часов
      path: '/',
    });

    return response;
  } catch (error) {
    console.error('Admin login error:', error);
    return NextResponse.json(
      { error: 'Ошибка сервера' },
      { status: 500 }
    );
  }
}

export async function GET() {
  return NextResponse.json({
    loginUrl: '/admin/login',
  });
}
