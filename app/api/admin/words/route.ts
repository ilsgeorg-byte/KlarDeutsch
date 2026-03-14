/**
 * API для управления словами
 * GET - список слов с пагинацией и фильтрами
 * POST - добавить новое слово
 */

import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:5000';
const POSTGRES_URL = process.env.POSTGRES_URL;

let pool: Pool | null = null;

function getPool() {
  if (!pool && POSTGRES_URL) {
    pool = new Pool({
      connectionString: POSTGRES_URL,
      ssl: POSTGRES_URL.includes('neon') ? { rejectUnauthorized: false } : false,
    });
  }
  return pool;
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const page = parseInt(searchParams.get('page') || '1');
    const limit = parseInt(searchParams.get('limit') || '50');
    const level = searchParams.get('level') || '';
    const search = searchParams.get('search') || '';
    const skip = (page - 1) * limit;

    // Пробуем через Flask API
    try {
      const params = new URLSearchParams({
        skip: String(skip),
        limit: String(limit),
      });
      if (level) params.set('level', level);

      const url = search
        ? `${API_BASE_URL}/api/words/search?q=${encodeURIComponent(search)}&limit=${limit}`
        : `${API_BASE_URL}/api/words?${params.toString()}`;

      const res = await fetch(url);

      if (res.ok) {
        const data = await res.json();
        return NextResponse.json(data);
      }
    } catch (apiError) {
      console.log('Flask API unavailable, using direct DB access');
    }

    // Если API недоступен - напрямую из БД
    const dbPool = getPool();
    if (!dbPool) {
      return NextResponse.json(
        { error: 'Database not configured' },
        { status: 500 }
      );
    }

    let query = '';
    let queryParams: any[] = [];

    if (search) {
      query = `
        SELECT id, level, topic, de, ru, article, verb_forms, example_de, example_ru, audio_url,
               plural, examples, synonyms, antonyms, collocations, false as is_favorite
        FROM words
        WHERE (de ILIKE $1 OR ru ILIKE $1)
        ORDER BY id
        LIMIT $2 OFFSET $3
      `;
      queryParams = [`%${search}%`, limit, skip];
    } else if (level) {
      query = `
        SELECT id, level, topic, de, ru, article, verb_forms, example_de, example_ru, audio_url,
               plural, examples, synonyms, antonyms, collocations, false as is_favorite
        FROM words
        WHERE level = $1
        ORDER BY id
        LIMIT $2 OFFSET $3
      `;
      queryParams = [level, limit, skip];
    } else {
      query = `
        SELECT id, level, topic, de, ru, article, verb_forms, example_de, example_ru, audio_url,
               plural, examples, synonyms, antonyms, collocations, false as is_favorite
        FROM words
        ORDER BY id
        LIMIT $1 OFFSET $2
      `;
      queryParams = [limit, skip];
    }

    const wordsResult = await dbPool.query(query, queryParams);
    
    // Получаем общее количество
    let countQuery = 'SELECT COUNT(*) FROM words';
    let countParams: any[] = [];
    if (search) {
      countQuery = 'SELECT COUNT(*) FROM words WHERE de ILIKE $1 OR ru ILIKE $1';
      countParams = [`%${search}%`];
    } else if (level) {
      countQuery = 'SELECT COUNT(*) FROM words WHERE level = $1';
      countParams = [level];
    }
    
    const countResult = await dbPool.query(countQuery, countParams);
    const total = parseInt(countResult.rows[0]?.count || '0');

    return NextResponse.json({
      data: wordsResult.rows,
      total,
      skip,
      limit,
    });
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

    // Пробуем через Flask API
    try {
      const res = await fetch(`${API_BASE_URL}/api/words/custom`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${process.env.ADMIN_API_TOKEN}`,
        },
        body: JSON.stringify(body),
      });

      if (res.ok) {
        const data = await res.json();
        return NextResponse.json(data);
      }
    } catch (apiError) {
      console.log('Flask API unavailable, using direct DB access');
    }

    // Если API недоступен - напрямую в БД
    const dbPool = getPool();
    if (!dbPool) {
      return NextResponse.json(
        { error: 'Database not configured' },
        { status: 500 }
      );
    }

    const { de, ru, article, level, topic, verb_forms, example_de, example_ru } = body;

    if (!de || !ru) {
      return NextResponse.json(
        { error: 'Поля de и ru обязательны' },
        { status: 400 }
      );
    }

    const result = await dbPool.query(
      `INSERT INTO words (de, ru, article, level, topic, verb_forms, example_de, example_ru)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
       RETURNING id`,
      [de, ru, article || '', level || 'A1', topic || '', verb_forms || '', example_de || '', example_ru || '']
    );

    const word_id = result.rows[0]?.id;

    return NextResponse.json({ status: 'success', word_id });
  } catch (error) {
    console.error('Admin words POST error:', error);
    return NextResponse.json(
      { error: 'Ошибка сервера' },
      { status: 500 }
    );
  }
}

export async function PUT(request: NextRequest) {
  try {
    const body = await request.json();
    const { id, de, ru, article, level, topic, verb_forms, example_de, example_ru } = body;

    if (!id) {
      return NextResponse.json(
        { error: 'ID слова обязателен' },
        { status: 400 }
      );
    }

    if (!de || !ru) {
      return NextResponse.json(
        { error: 'Поля de и ru обязательны' },
        { status: 400 }
      );
    }

    // Пробуем через Flask API (если есть endpoint для обновления)
    try {
      const res = await fetch(`${API_BASE_URL}/api/admin/words/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${process.env.ADMIN_API_TOKEN}`,
        },
        body: JSON.stringify(body),
      });

      if (res.ok) {
        const data = await res.json();
        return NextResponse.json(data);
      }
    } catch (apiError) {
      console.log('Flask API unavailable, using direct DB access');
    }

    // Если API недоступен - напрямую в БД
    const dbPool = getPool();
    if (!dbPool) {
      return NextResponse.json(
        { error: 'Database not configured' },
        { status: 500 }
      );
    }

    const result = await dbPool.query(
      `UPDATE words 
       SET de = $1, ru = $2, article = $3, level = $4, topic = $5, 
           verb_forms = $6, example_de = $7, example_ru = $8
       WHERE id = $9
       RETURNING id`,
      [de, ru, article || '', level || 'A1', topic || '', 
       verb_forms || '', example_de || '', example_ru || '', id]
    );

    if (result.rowCount === 0) {
      return NextResponse.json(
        { error: 'Слово не найдено' },
        { status: 404 }
      );
    }

    return NextResponse.json({ status: 'success', word_id: id });
  } catch (error) {
    console.error('Admin words PUT error:', error);
    return NextResponse.json(
      { error: 'Ошибка сервера: ' + (error instanceof Error ? error.message : String(error)) },
      { status: 500 }
    );
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');

    if (!id) {
      return NextResponse.json(
        { error: 'ID слова обязателен' },
        { status: 400 }
      );
    }

    // Пробуем через Flask API
    try {
      const res = await fetch(`${API_BASE_URL}/api/admin/words/${id}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${process.env.ADMIN_API_TOKEN}`,
        },
      });

      if (res.ok) {
        const data = await res.json();
        return NextResponse.json(data);
      }
    } catch (apiError) {
      console.log('Flask API unavailable, using direct DB access');
    }

    // Если API недоступен - напрямую из БД
    const dbPool = getPool();
    if (!dbPool) {
      return NextResponse.json(
        { error: 'Database not configured' },
        { status: 500 }
      );
    }

    const result = await dbPool.query('DELETE FROM words WHERE id = $1', [id]);

    if (result.rowCount === 0) {
      return NextResponse.json(
        { error: 'Слово не найдено' },
        { status: 404 }
      );
    }

    return NextResponse.json({ status: 'success' });
  } catch (error) {
    console.error('Admin words DELETE error:', error);
    return NextResponse.json(
      { error: 'Ошибка сервера' },
      { status: 500 }
    );
  }
}
