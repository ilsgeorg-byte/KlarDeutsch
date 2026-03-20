/**
 * API для управления словами
 * GET - список слов с пагинацией и фильтрами
 * POST - добавить новое слово
 */

import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:5000';
const POSTGRES_URL = process.env.POSTGRES_URL || '';

let pool: Pool | null = null;

function getPool() {
  if (!pool && POSTGRES_URL) {
    // Проверяем тип подключения
    const isNeon = POSTGRES_URL.includes('neon') || POSTGRES_URL.includes('supabase');

    console.log('Creating DB pool, isNeon:', isNeon);

    // Добавляем sslmode=verify-full для подавления предупреждения
    let connectionString = POSTGRES_URL;
    if (!connectionString.includes('sslmode=')) {
      const separator = connectionString.includes('?') ? '&' : '?';
      connectionString = `${connectionString}${separator}sslmode=verify-full`;
    }

    pool = new Pool({
      connectionString,
      ssl: isNeon ? { rejectUnauthorized: false } : undefined,
    });

    console.log('DB pool created successfully');
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
    console.log('=== POST /api/admin/words START ===');
    console.log('Request body:', body);
    console.log('POSTGRES_URL set:', !!POSTGRES_URL);

    // Используем прямой доступ к БД (для Vercel)
    const dbPool = getPool();
    console.log('DB pool created:', !!dbPool);
    
    if (!dbPool) {
      console.error('Database not configured');
      return NextResponse.json(
        { error: 'Database not configured' },
        { status: 500 }
      );
    }

    const { de, ru, article, level, topic, verb_forms, plural, example_de, example_ru, synonyms, antonyms, collocations } = body;

    if (!de || !ru) {
      console.error('Missing de or ru');
      return NextResponse.json(
        { error: 'Поля de и ru обязательны' },
        { status: 400 }
      );
    }

    console.log('Executing INSERT query...');
    
    const result = await dbPool.query(
      `INSERT INTO words (de, ru, article, level, topic, verb_forms, plural, example_de, example_ru, synonyms, antonyms, collocations)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
       RETURNING id`,
      [de, ru, article || '', level || 'A1', topic || '', verb_forms || '', plural || '', example_de || '', example_ru || '', synonyms || '', antonyms || '', collocations || '']
    );

    console.log('INSERT result:', result.rows[0]);
    console.log('=== POST /api/admin/words SUCCESS ===');

    const word_id = result.rows[0]?.id;

    return NextResponse.json({ status: 'success', word_id });
  } catch (error) {
    console.error('=== POST /api/admin/words ERROR ===');
    console.error('Admin words POST error:', error);
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.error('Error message:', errorMessage);
    console.error('Error stack:', error instanceof Error ? error.stack : 'no stack');
    return NextResponse.json(
      { error: 'Ошибка сервера: ' + errorMessage },
      { status: 500 }
    );
  }
}

export async function PUT(request: NextRequest) {
  console.log('=== PUT /api/admin/words START ===');

  try {
    const body = await request.json();
    console.log('PUT request body:', body);
    
    const id = body.id;
    const de = body.de;
    const ru = body.ru;
    const article = body.article ?? '';
    const level = body.level ?? 'A1';
    const topic = body.topic ?? '';
    const verb_forms = body.verb_forms ?? '';
    const plural = body.plural ?? '';
    const example_de = body.example_de ?? '';
    const example_ru = body.example_ru ?? '';
    const synonyms = body.synonyms ?? '';
    const antonyms = body.antonyms ?? '';
    const collocations = body.collocations ?? '';

    console.log('PUT /api/admin/words:', { id, de, ru, level });

    if (!id) {
      console.error('PUT error: missing id');
      return NextResponse.json(
        { error: 'ID слова обязателен' },
        { status: 400 }
      );
    }

    if (!de || !ru) {
      console.error('PUT error: missing de or ru');
      return NextResponse.json(
        { error: 'Поля de и ru обязательны' },
        { status: 400 }
      );
    }

    // Прямой доступ к базе данных
    console.log('POSTGRES_URL set:', !!POSTGRES_URL);

    if (!POSTGRES_URL) {
      console.error('Database not configured');
      return NextResponse.json(
        { error: 'Database not configured' },
        { status: 500 }
      );
    }

    const pool = getPool();
    console.log('DB pool created:', !!pool);

    if (!pool) {
      console.error('Database pool not created');
      return NextResponse.json(
        { error: 'Database not configured' },
        { status: 500 }
      );
    }

    console.log('Executing UPDATE query...');

    // Проверяем, существует ли слово с такими de и ru (кроме текущего)
    // Но только если de или ru изменились
    const currentWord = await pool.query(
      `SELECT de, ru FROM words WHERE id = $1`,
      [id]
    );

    if (currentWord.rowCount && currentWord.rowCount > 0) {
      const oldDe = currentWord.rows[0].de;
      const oldRu = currentWord.rows[0].ru;

      // Если de или ru изменились, проверяем на дубликаты
      if (de !== oldDe || ru !== oldRu) {
        const checkResult = await pool.query(
          `SELECT id FROM words WHERE de = $1 AND ru = $2 AND id != $3`,
          [de, ru, id]
        );

        if (checkResult.rowCount && checkResult.rowCount > 0) {
          console.log('Duplicate found:', checkResult.rows[0]);
          return NextResponse.json(
            { error: 'Слово с такими de и ru уже существует' },
            { status: 400 }
          );
        }
      }
    }

    const updateResult = await pool.query(
      `UPDATE words
       SET de = $1, ru = $2, article = $3, level = $4, topic = $5,
           verb_forms = $6, plural = $7, example_de = $8, example_ru = $9,
           synonyms = $10, antonyms = $11, collocations = $12
       WHERE id = $13
       RETURNING id`,
      [de, ru, article, level, topic, verb_forms, plural, example_de, example_ru, synonyms, antonyms, collocations, id]
    );

    console.log('UPDATE result:', { rowCount: updateResult.rowCount, rows: updateResult.rows });

    if (updateResult.rowCount === 0) {
      return NextResponse.json(
        { error: 'Слово не найдено' },
        { status: 404 }
      );
    }

    console.log('=== PUT /api/admin/words SUCCESS ===');
    return NextResponse.json({ status: 'success', word_id: id });
  } catch (error) {
    console.error('=== PUT /api/admin/words ERROR ===');
    console.error('Admin words PUT error:', error);
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.error('Error message:', errorMessage);
    console.error('Error stack:', error instanceof Error ? error.stack : 'no stack');
    return NextResponse.json(
      { error: 'Ошибка сервера: ' + errorMessage },
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
