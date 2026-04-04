/**
 * API для управления пользователями
 * GET - список пользователей
 */

import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:5000';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const page = searchParams.get('page') || '1';
    const limit = searchParams.get('limit') || '20';
    const search = searchParams.get('search') || '';

    // Запрос к Flask API за пользователями
    const url = search
      ? `${API_BASE_URL}/api/admin/users/search?q=${encodeURIComponent(search)}`
      : `${API_BASE_URL}/api/admin/users?page=${page}&limit=${limit}`;

    const res = await fetch(url, {
      headers: {
        Authorization: `Bearer ${process.env.ADMIN_API_TOKEN || ''}`,
      },
    });

    if (!res.ok) {
      // Если админ API нет, возвращаем заглушку
      if (res.status === 404) {
        return NextResponse.json({
          users: [],
          total: 0,
          page: parseInt(page),
          limit: parseInt(limit),
        });
      }

      return NextResponse.json(
        { error: 'Ошибка получения пользователей' },
        { status: res.status }
      );
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Admin users GET error:', error);
    return NextResponse.json(
      {
        users: [],
        total: 0,
        page: 1,
        limit: 20,
      },
      { status: 200 }
    );
  }
}
