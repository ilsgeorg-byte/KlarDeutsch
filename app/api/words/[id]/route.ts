/**
 * API для получения слова по ID
 * GET - одно слово с деталями
 */

import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';

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
  
  if (authHeader.startsWith('Bearer ')) {
    return authHeader.substring(7);
  }
  return authHeader;
}

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

export async function GET(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const wordId = parseInt(params.id);
    
    if (isNaN(wordId)) {
      return NextResponse.json(
        { error: 'Неверный ID слова' },
        { status: 400 }
      );
    }

    const token = getToken(request);
    let user_id: number | null = null;
    
    if (token) {
      const decoded = decodeJWT(token);
      if (!decoded.error) {
        user_id = decoded.user_id;
      }
    }

    const dbPool = getPool();
    
    if (!dbPool) {
      return NextResponse.json(
        { error: 'База данных не настроена' },
        { status: 500 }
      );
    }

    // Получаем слово
    let query = `
      SELECT id, level, topic, de, ru, article, verb_forms, example_de, example_ru, audio_url,
             plural, examples, synonyms, antonyms, collocations,
             false as is_favorite
      FROM words
      WHERE id = $1
    `;
    let queryParams: any[] = [wordId];

    // Если пользователь авторизован, проверяем избранное и личные слова
    if (user_id) {
      query = `
        SELECT w.id, w.level, w.topic, w.de, w.ru, w.article, w.verb_forms, w.example_de, w.example_ru, w.audio_url,
               w.plural, w.examples, w.synonyms, w.antonyms, w.collocations,
               (f.word_id IS NOT NULL) as is_favorite
        FROM words w
        LEFT JOIN user_favorites f ON w.id = f.word_id AND f.user_id = $2
        WHERE w.id = $1 AND (w.user_id IS NULL OR w.user_id = $2)
      `;
      queryParams = [wordId, user_id];
    } else {
      // Для неавторизованных - только общие слова
      query += ' AND user_id IS NULL';
    }

    const result = await dbPool.query(query, queryParams);

    if (result.rowCount === 0) {
      return NextResponse.json(
        { error: 'Слово не найдено' },
        { status: 404 }
      );
    }

    return NextResponse.json(result.rows[0]);
  } catch (error) {
    console.error('Word detail GET error:', error);
    return NextResponse.json(
      { error: 'Ошибка сервера: ' + (error instanceof Error ? error.message : String(error)) },
      { status: 500 }
    );
  }
}
