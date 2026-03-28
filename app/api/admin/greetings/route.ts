/**
 * API для удаления конструкций приветствий
 * GET - получить список конструкций для удаления
 * POST - удалить найденные конструкции
 */

import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';

const POSTGRES_URL = process.env.POSTGRES_URL || '';

const GREETING_PATTERNS = [
  '^guten\\s+tag$',
  '^guten\\s+abend$',
  '^guten\\s+morgen$',
  '^gute\\s+nacht$',
  '^guten\\s+rutsch$',
  '^frohe\\s+weihnachten$',
  '^frohe\\s+ostern$',
  '^herzlichen\\s+glückwunsch',
  '^guten\\s+appetit$',
  '^auf\\s+wiedersehen$',
  '^machs?\\s+gut$',
  '^bis\\s+bald$',
  '^bis\\s+morgen$',
  '^bis\\s+später$',
];

function getPool() {
  if (!POSTGRES_URL) return null;
  
  const isNeon = POSTGRES_URL.includes('neon') || POSTGRES_URL.includes('supabase');
  let connectionString = POSTGRES_URL;
  if (!connectionString.includes('sslmode=')) {
    const separator = connectionString.includes('?') ? '&' : '?';
    connectionString = `${connectionString}${separator}sslmode=verify-full`;
  }

  return new Pool({
    connectionString,
    ssl: isNeon ? { rejectUnauthorized: false } : undefined,
  });
}

// GET - получить список конструкций для удаления
export async function GET() {
  try {
    const pool = getPool();
    if (!pool) {
      return NextResponse.json({ error: 'БД не подключена' }, { status: 500 });
    }

    // Собираем все паттерны в один запрос
    const conditions = GREETING_PATTERNS.map(pattern => 
      `de ~* '${pattern}'`
    ).join(' OR ');

    const query = `
      SELECT id, level, de, ru, article
      FROM words
      WHERE ${conditions}
      ORDER BY id
    `;

    const result = await pool.query(query);
    await pool.end();

    return NextResponse.json({
      total: result.rows.length,
      words: result.rows,
    });
  } catch (error) {
    console.error('Get greetings error:', error);
    return NextResponse.json(
      { error: 'Ошибка: ' + (error instanceof Error ? error.message : String(error)) },
      { status: 500 }
    );
  }
}

// POST - удалить конструкции
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { deleteAll = false, ids = [] } = body || {};

    const pool = getPool();
    if (!pool) {
      return NextResponse.json({ error: 'БД не подключена' }, { status: 500 });
    }

    let deletedCount = 0;

    if (deleteAll) {
      // Удаляем все конструкции по паттернам
      const conditions = GREETING_PATTERNS.map(pattern => 
        `de ~* '${pattern}'`
      ).join(' OR ');

      const result = await pool.query(`
        DELETE FROM words
        WHERE ${conditions}
      `);
      deletedCount = result.rowCount || 0;
    } else if (ids.length > 0) {
      // Удаляем по указанным ID
      const placeholders = ids.map((_: any, i: number) => `$${i + 1}`).join(',');
      const result = await pool.query(`
        DELETE FROM words
        WHERE id IN (${placeholders})
      `, ids);
      deletedCount = result.rowCount || 0;
    }

    await pool.end();

    return NextResponse.json({
      success: true,
      deletedCount,
      message: `Удалено ${deletedCount} конструкций`,
    });
  } catch (error) {
    console.error('Delete greetings error:', error);
    return NextResponse.json(
      { error: 'Ошибка: ' + (error instanceof Error ? error.message : String(error)) },
      { status: 500 }
    );
  }
}
