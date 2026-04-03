/**
 * Статистика для дашборда админа
 */

import { NextResponse } from 'next/server';
import { Pool } from 'pg';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:5000';
const POSTGRES_URL = process.env.POSTGRES_URL || '';

// Создаём пул подключений к БД (глобальный, переиспользуется)
let pool: Pool | null = null;

function getPool() {
  if (!pool && POSTGRES_URL) {
    pool = new Pool({
      connectionString: POSTGRES_URL,
      ssl: POSTGRES_URL.includes('neon') ? { rejectUnauthorized: false } : undefined,
    });
  }
  return pool;
}

export async function GET() {
  try {
    // Пробуем получить данные из Flask API
    const token = process.env.ADMIN_API_TOKEN;
    
    const [wordsRes, usersRes, diaryRes] = await Promise.all([
      fetch(`${API_BASE_URL}/api/admin/stats/words`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      }).catch(() => null),
      fetch(`${API_BASE_URL}/api/admin/stats/users`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      }).catch(() => null),
      fetch(`${API_BASE_URL}/api/admin/stats/diary`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      }).catch(() => null),
    ]);

    // Если API вернул данные - используем их
    if (wordsRes?.ok && usersRes?.ok && diaryRes?.ok) {
      const wordsData = await wordsRes.json();
      const usersData = await usersRes.json();
      const diaryData = await diaryRes.json();
      
      return NextResponse.json({
        words: wordsData,
        users: usersData,
        diary: diaryData,
        timestamp: new Date().toISOString(),
      });
    }

    // Если API недоступен - пробуем напрямую из БД
    console.log('Flask API stats unavailable, querying database directly');
    
    const dbPool = getPool();
    
    if (!dbPool) {
      console.warn('POSTGRES_URL not configured, returning empty stats');
      return NextResponse.json({
        words: { total: 0, by_level: {} },
        users: { total: 0, active_today: 0 },
        diary: { total_entries: 0, today: 0 },
        timestamp: new Date().toISOString(),
      });
    }

    // Получаем статистику напрямую из БД
    const wordsResult = await dbPool.query('SELECT level, COUNT(*) FROM words GROUP BY level');
    const usersResult = await dbPool.query('SELECT COUNT(*) FROM users');
    const diaryResult = await dbPool.query('SELECT COUNT(*) FROM diary_entries');

    const wordsByLevel: Record<string, number> = {};
    let totalWords = 0;
    
    for (const row of wordsResult.rows) {
      wordsByLevel[row.level] = parseInt(row.count);
      totalWords += parseInt(row.count);
    }

    const totalUsers = parseInt(usersResult.rows[0]?.count || '0');
    const totalDiary = parseInt(diaryResult.rows[0]?.count || '0');

    return NextResponse.json({
      words: { total: totalWords, by_level: wordsByLevel },
      users: { total: totalUsers, active_today: 0 },
      diary: { total_entries: totalDiary, today: 0 },
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Admin stats error:', error);
    return NextResponse.json(
      {
        words: { total: 0, by_level: {} },
        users: { total: 0, active_today: 0 },
        diary: { total_entries: 0, today: 0 },
        timestamp: new Date().toISOString(),
      },
      { status: 200 }
    );
  }
}
