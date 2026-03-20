/**
 * API для массовой загрузки слов
 * POST - загрузка слов из JSON/CSV файла или массива
 */

import { NextRequest, NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:5000';

export async function POST(request: NextRequest) {
  try {
    const token = request.headers.get('authorization');
    
    // Проверяем тип контента
    const contentType = request.headers.get('content-type') || '';
    
    let apiUrl = `${API_BASE_URL}/api/words/bulk-upload`;
    let fetchOptions: RequestInit = {
      method: 'POST',
      headers: {},
      body: undefined,
    };

    if (contentType.includes('multipart/form-data')) {
      // Загрузка файла
      const formData = await request.formData();
      fetchOptions.body = formData;
      // Заголовки будут установлены автоматически браузером для FormData
    } else if (contentType.includes('application/json')) {
      // JSON данные
      const jsonData = await request.json();
      fetchOptions.headers = {
        'Content-Type': 'application/json',
      };
      fetchOptions.body = JSON.stringify(jsonData);
    } else {
      return NextResponse.json(
        { error: 'Неподдерживаемый формат данных' },
        { status: 400 }
      );
    }

    // Добавляем токен авторизации
    if (token) {
      (fetchOptions.headers as Record<string, string>)['Authorization'] = token;
    }

    const response = await fetch(apiUrl, fetchOptions);
    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { error: data.error || 'Ошибка при загрузке слов' },
        { status: response.status }
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error('Bulk upload error:', error);
    return NextResponse.json(
      { error: 'Ошибка сервера' },
      { status: 500 }
    );
  }
}
