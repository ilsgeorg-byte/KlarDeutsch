/**
 * API для просмотра последних проверенных слов
 * GET - получить последние проверенные слова
 */

import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';

export const dynamic = 'force-dynamic';

const POSTGRES_URL = process.env.POSTGRES_URL || '';

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

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const limit = parseInt(searchParams.get('limit') || '50');
    const checked = searchParams.get('checked') === 'true'; // true = проверенные, false = непроверенные

    const pool = getPool();
    if (!pool) {
      return NextResponse.json({ error: 'БД не подключена' }, { status: 500 });
    }

    let query: string;
    if (checked) {
      // Последние проверенные
      query = `
        SELECT id, level, de, ru, article, verb_forms, ai_checked_at
        FROM words
        WHERE ai_checked_at IS NOT NULL
        ORDER BY ai_checked_at DESC
        LIMIT $1
      `;
    } else {
      // Непроверенные
      query = `
        SELECT id, level, de, ru, article, verb_forms, ai_checked_at
        FROM words
        WHERE ai_checked_at IS NULL
        ORDER BY id
        LIMIT $1
      `;
    }

    const result = await pool.query(query, [limit]);
    await pool.end();

    return NextResponse.json({
      total: result.rows.length,
      words: result.rows,
    });
  } catch (error) {
    console.error('Checked words error:', error);
    return NextResponse.json(
      { error: 'Ошибка: ' + (error instanceof Error ? error.message : String(error)) },
      { status: 500 }
    );
  }
}
