/**
 * Статистика для дашборда админа
 */

import { NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:5000';

export async function GET() {
  try {
    const token = process.env.ADMIN_API_TOKEN; // Токен для внутренних запросов

    // Параллельно запрашиваем всю статистику
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

    // Собираем данные (с fallback если API недоступен)
    const wordsData = wordsRes?.ok ? await wordsRes.json() : { total: 0, by_level: {} };
    const usersData = usersRes?.ok ? await usersRes.json() : { total: 0, active_today: 0 };
    const diaryData = diaryRes?.ok ? await diaryRes.json() : { total_entries: 0, today: 0 };

    return NextResponse.json({
      words: wordsData,
      users: usersData,
      diary: diaryData,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Admin stats error:', error);
    return NextResponse.json(
      {
        words: { total: 0, by_level: {} },
        users: { total: 0, active_today: 0 },
        diary: { total_entries: 0, today: 0 },
      },
      { status: 200 } // Возвращаем пустые данные вместо ошибки
    );
  }
}
