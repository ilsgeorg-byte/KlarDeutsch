/**
 * API для получения личных слов пользователя
 * GET - список личных слов с пагинацией
 */

import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:5000';
const POSTGRES_URL = process.env.POSTGRES_URL || '';

let pool: Pool | null = null;

function getPool() {
  if (!pool && POSTGRES_URL) {
    const isNeon = POSTGRES_URL.includes('neon') || POSTGRES_URL.includes('supabase');
    
    let connectionString = POSTGRES_URL;
    if (!connectionString.includes('sslmode=')) {
      const separator = connectionString.includes('?') ? '&' : '?';
      connectionString = `${connectionString}${separator}sslmode=verify-full`;
    }

    pool = new Pool({
      connectionString,
      ssl: isNeon ? { rejectUnauthorized: false } : undefined,
    });
  }
  return pool;
}

function getToken(request: NextRequest): string | null {
  const authHeader = request.headers.get('authorization');
  if (!authHeader) return null;
  
  // Поддерживаем оба формата: "Bearer <token>" и просто "<token>"
  if (authHeader.startsWith('Bearer ')) {
    return authHeader.substring(7);
  }
  return authHeader;
}

// Декодирование JWT токена для получения user_id
function decodeJWT(token: string): { user_id: number | null; error: string | null } {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) {
      return { user_id: null, error: 'Неверный формат токена' };
    }

    const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')));
    
    if (payload.exp && payload.exp < Date.now() / 1000) {
      return { user_id: null, error: 'Токен истёк' };
    }

    return { user_id: payload.user_id || null, error: null };
  } catch (error) {
    return { user_id: null, error: 'Ошибка декодирования токена' };
  }
}

export async function GET(request: NextRequest) {
  try {
    const token = getToken(request);
    
    if (!token) {
      return NextResponse.json(
        { error: 'Требуется авторизация' },
        { status: 401 }
      );
    }

    // Декодируем токен для получения user_id
    const { user_id, error } = decodeJWT(token);
    
    if (error || !user_id) {
      return NextResponse.json(
        { error: error || 'Неверный токен' },
        { status: 401 }
      );
    }

    const { searchParams } = new URL(request.url);
    const page = parseInt(searchParams.get('page') || '1');
    const limit = parseInt(searchParams.get('limit') || '50');
    const level = searchParams.get('level') || '';
    const skip = (page - 1) * limit;

    const dbPool = getPool();
    
    if (!dbPool) {
      return NextResponse.json(
        { error: 'База данных не настроена' },
        { status: 500 }
      );
    }

    // Общее количество
    let countQuery = 'SELECT COUNT(*) FROM words WHERE user_id = $1';
    let countParams: any[] = [user_id];
    
    if (level) {
      countQuery += ' AND level = $2';
      countParams = [user_id, level];
    }

    const countResult = await dbPool.query(countQuery, countParams);
    const total = parseInt(countResult.rows[0]?.count || '0');

    // Получаем слова
    let query = `
      SELECT id, level, topic, de, ru, article, verb_forms, example_de, example_ru, audio_url,
             plural, examples, synonyms, antonyms, collocations,
             true as is_favorite
      FROM words
      WHERE user_id = $1
    `;
    let queryParams: any[] = [user_id];
    
    if (level) {
      query += ' AND level = $2';
      queryParams = [user_id, level];
    }
    
    query += ' ORDER BY id DESC LIMIT $' + (queryParams.length + 1) + ' OFFSET $' + (queryParams.length + 2);
    queryParams.push(limit, skip);

    const result = await dbPool.query(query, queryParams);

    return NextResponse.json({
      data: result.rows,
      total,
      skip,
      limit,
    });
  } catch (error) {
    console.error('My words GET error:', error);
    return NextResponse.json(
      { error: 'Ошибка сервера: ' + (error instanceof Error ? error.message : String(error)) },
      { status: 500 }
    );
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const token = getToken(request);
    
    if (!token) {
      return NextResponse.json(
        { error: 'Требуется авторизация' },
        { status: 401 }
      );
    }

    const { user_id, error } = decodeJWT(token);
    
    if (error || !user_id) {
      return NextResponse.json(
        { error: error || 'Неверный токен' },
        { status: 401 }
      );
    }

    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');

    if (!id) {
      return NextResponse.json(
        { error: 'ID слова обязателен' },
        { status: 400 }
      );
    }

    const dbPool = getPool();
    
    if (!dbPool) {
      return NextResponse.json(
        { error: 'База данных не настроена' },
        { status: 500 }
      );
    }

    // Проверяем, что слово принадлежит пользователю
    const checkResult = await dbPool.query(
      'SELECT user_id FROM words WHERE id = $1',
      [id]
    );

    if (checkResult.rowCount === 0) {
      return NextResponse.json(
        { error: 'Слово не найдено' },
        { status: 404 }
      );
    }

    if (checkResult.rows[0]?.user_id !== user_id) {
      return NextResponse.json(
        { error: 'Нет прав для удаления этого слова' },
        { status: 403 }
      );
    }

    // Удаляем слово
    await dbPool.query(
      'DELETE FROM words WHERE id = $1 AND user_id = $2',
      [id, user_id]
    );

    return NextResponse.json({ status: 'success', word_id: id });
  } catch (error) {
    console.error('My words DELETE error:', error);
    return NextResponse.json(
      { error: 'Ошибка сервера: ' + (error instanceof Error ? error.message : String(error)) },
      { status: 500 }
    );
  }
}
