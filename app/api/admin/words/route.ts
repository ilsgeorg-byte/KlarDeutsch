/**
 * API для управления словами
 * GET - список слов с пагинацией и фильтрами
 * POST - добавить новое слово
 */

import { NextRequest, NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:5000';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const page = searchParams.get('page') || '1';
    const limit = searchParams.get('limit') || '50';
    const level = searchParams.get('level') || '';
    const search = searchParams.get('search') || '';

    const params = new URLSearchParams({
      skip: String((parseInt(page) - 1) * parseInt(limit)),
      limit,
    });

    if (level) params.set('level', level);

    const url = search
      ? `${API_BASE_URL}/api/words/search?q=${encodeURIComponent(search)}&limit=${limit}`
      : `${API_BASE_URL}/api/words?${params.toString()}`;

    const res = await fetch(url);

    if (!res.ok) {
      return NextResponse.json(
        { error: 'Ошибка получения слов' },
        { status: res.status }
      );
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Admin words GET error:', error);
    return NextResponse.json(
      { error: 'Ошибка сервера' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const res = await fetch(`${API_BASE_URL}/api/words/custom`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // Токен админа для API
        Authorization: `Bearer ${process.env.ADMIN_API_TOKEN}`,
      },
      body: JSON.stringify(body),
    });

    const data = await res.json();

    if (!res.ok) {
      return NextResponse.json(
        { error: data.error || 'Ошибка добавления слова' },
        { status: res.status }
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error('Admin words POST error:', error);
    return NextResponse.json(
      { error: 'Ошибка сервера' },
      { status: 500 }
    );
  }
}
