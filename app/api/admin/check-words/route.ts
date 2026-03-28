/**
 * API для запуска AI проверки слов
 * POST - запустить проверку
 * GET - получить статус последней проверки
 */

import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';
import { spawn } from 'child_process';
import path from 'path';

const POSTGRES_URL = process.env.POSTGRES_URL || '';
const GROQ_API_KEY = process.env.GROQ_API_KEY || '';

// Хранилище статуса последней проверки (в памяти)
let checkStatus: {
  running: boolean;
  lastRun: Date | null;
  totalChecked: number;
  errorsFound: number;
  translationsAdded: number;
  greetingConstructions: number;
  message: string;
} = {
  running: false,
  lastRun: null,
  totalChecked: 0,
  errorsFound: 0,
  translationsAdded: 0,
  greetingConstructions: 0,
  message: 'Ожидание запуска',
};

function getPool() {
  if (!POSTGRES_URL) {
    return null;
  }
  
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

/**
 * Запускает Python скрипт проверки слов
 */
async function runWordCheck(limit: number = 500): Promise<void> {
  if (checkStatus.running) {
    return;
  }

  checkStatus.running = true;
  checkStatus.message = 'Запуск проверки...';

  return new Promise((resolve) => {
    // Путь к скрипту - используем абсолютный путь для Windows
    const scriptPath = path.join(process.cwd(), 'tools', 'check_words_ai.py');
    
    console.log('[check-words] Script path:', scriptPath);
    console.log('[check-words] CWD:', process.cwd());

    // Проверяем существование скрипта
    const fs = require('fs');
    if (!fs.existsSync(scriptPath)) {
      checkStatus.message = `Ошибка: скрипт не найден: ${scriptPath}`;
      checkStatus.running = false;
      console.error('[check-words] Script not found:', scriptPath);
      resolve();
      return;
    }

    // Пробуем разные команды для Python
    const pythonCommands = ['python', 'python3', 'py'];
    let selectedCommand = pythonCommands[0];
    
    // Проверяем, какая команда доступна
    const { execSync } = require('child_process');
    for (const cmd of pythonCommands) {
      try {
        execSync(`${cmd} --version`, { stdio: 'pipe' });
        selectedCommand = cmd;
        console.log('[check-words] Using Python command:', cmd);
        break;
      } catch (e) {
        continue;
      }
    }

    // Создаём процесс Python для Windows
    // Используем cmd.exe /c для корректного запуска
    const pythonProcess = spawn('cmd.exe', ['/c', selectedCommand, scriptPath], {
      env: {
        ...process.env,
        POSTGRES_URL: POSTGRES_URL || '',
        GROQ_API_KEY: GROQ_API_KEY || '',
        PYTHONIOENCODING: 'utf-8',
        PYTHONUTF8: '1',
      },
      cwd: process.cwd(),
      detached: false,
      windowsHide: true,
    });

    let output = '';
    let errorOutput = '';

    pythonProcess.stdout?.on('data', (data) => {
      const text = data.toString();
      output += text;
      console.log('[check-words]', text.trim());

      // Парсим прогресс из вывода
      const progressMatch = text.match(/Проверено: (\d+)\/(\d+)/);
      if (progressMatch) {
        const current = parseInt(progressMatch[1]);
        checkStatus.message = `Проверка: ${current} слов...`;
      }
    });

    pythonProcess.stderr?.on('data', (data) => {
      const text = data.toString();
      errorOutput += text;
      console.error('[check-words error]', text.trim());
    });

    pythonProcess.on('error', (err) => {
      checkStatus.running = false;
      checkStatus.message = `Ошибка запуска Python: ${err.message}`;
      console.error('[check-words] Process error:', err);
      resolve();
    });

    pythonProcess.on('close', (code) => {
      checkStatus.running = false;
      checkStatus.lastRun = new Date();
      
      console.log('[check-words] Process closed with code:', code);
      console.log('[check-words] Error output:', errorOutput);

      if (code === 0) {
        // Парсим итоги из вывода
        const totalMatch = output.match(/Всего проверено: (\d+)/);
        const errorsMatch = output.match(/Ошибки: (\d+)/);
        const translationsMatch = output.match(/Добавлено переводов: (\d+)/);
        const greetingMatch = output.match(/Конструкции приветствий: (\d+)/);

        checkStatus.totalChecked = totalMatch ? parseInt(totalMatch[1]) : 0;
        checkStatus.errorsFound = errorsMatch ? parseInt(errorsMatch[1]) : 0;
        checkStatus.translationsAdded = translationsMatch ? parseInt(translationsMatch[1]) : 0;
        checkStatus.greetingConstructions = greetingMatch ? parseInt(greetingMatch[1]) : 0;
        checkStatus.message = `Проверка завершена. Найдено ошибок: ${checkStatus.errorsFound}`;
      } else {
        checkStatus.message = `Ошибка проверки (код ${code}): ${errorOutput.slice(0, 500)}`;
      }

      resolve();
    });

    // Таймаут на случай зависания
    setTimeout(() => {
      if (checkStatus.running) {
        pythonProcess.kill();
        checkStatus.running = false;
        checkStatus.message = 'Таймаут проверки (5 минут)';
        resolve();
      }
    }, 5 * 60 * 1000); // 5 минут
  });
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { limit = 500, dry_run = false } = body || {};

    console.log('=== POST /api/admin/check-words ===');
    console.log('Params:', { limit, dry_run });

    // Проверяем переменные окружения
    if (!POSTGRES_URL) {
      return NextResponse.json(
        { error: 'POSTGRES_URL не настроен' },
        { status: 500 }
      );
    }

    if (!GROQ_API_KEY) {
      return NextResponse.json(
        { error: 'GROQ_API_KEY не настроен' },
        { status: 500 }
      );
    }

    // Проверяем, не запущена ли уже проверка
    if (checkStatus.running) {
      return NextResponse.json({
        status: 'already_running',
        message: 'Проверка уже запущена',
        currentStatus: checkStatus,
      });
    }

    // Запускаем проверку (асинхронно, не ожидая завершения)
    // В реальном приложении лучше использовать очередь задач
    runWordCheck(limit).catch(console.error);

    return NextResponse.json({
      status: 'started',
      message: `Запущена проверка ${limit} слов`,
      dry_run,
    });
  } catch (error) {
    console.error('Check words error:', error);
    return NextResponse.json(
      { error: 'Ошибка сервера: ' + (error instanceof Error ? error.message : String(error)) },
      { status: 500 }
    );
  }
}

export async function GET() {
  try {
    // Возвращаем текущий статус проверки
    return NextResponse.json({
      running: checkStatus.running,
      lastRun: checkStatus.lastRun,
      totalChecked: checkStatus.totalChecked,
      errorsFound: checkStatus.errorsFound,
      translationsAdded: checkStatus.translationsAdded,
      greetingConstructions: checkStatus.greetingConstructions,
      message: checkStatus.message,
    });
  } catch (error) {
    console.error('Check words status error:', error);
    return NextResponse.json(
      { error: 'Ошибка сервера' },
      { status: 500 }
    );
  }
}

/**
 * Сбрасывает статус проверки слов (ai_checked_at = NULL)
 */
export async function DELETE(request: NextRequest) {
  try {
    const body = await request.json();
    const { all = false } = body || {};

    console.log('=== DELETE /api/admin/check-words ===');
    console.log('Params:', { all });

    if (!POSTGRES_URL) {
      return NextResponse.json(
        { error: 'POSTGRES_URL не настроен' },
        { status: 500 }
      );
    }

    const pool = getPool();
    if (!pool) {
      return NextResponse.json(
        { error: 'Не удалось подключиться к БД' },
        { status: 500 }
      );
    }

    let result;
    
    if (all) {
      // Сбросить ВСЕ проверенные слова
      result = await pool.query(`
        UPDATE words SET ai_checked_at = NULL
      `);
    } else {
      // Сбросить только последние проверенные (500 шт)
      result = await pool.query(`
        UPDATE words SET ai_checked_at = NULL
        WHERE ai_checked_at IS NOT NULL
        ORDER BY ai_checked_at DESC
        LIMIT 500
      `);
    }

    const resetCount = result?.rowCount || 0;

    // Сбрасываем статус
    checkStatus.totalChecked = 0;
    checkStatus.errorsFound = 0;
    checkStatus.translationsAdded = 0;
    checkStatus.greetingConstructions = 0;
    checkStatus.message = 'Статус сброшен';

    return NextResponse.json({
      status: 'success',
      message: `Сброшено ${resetCount} слов`,
      resetCount,
    });
  } catch (error) {
    console.error('Check words reset error:', error);
    return NextResponse.json(
      { error: 'Ошибка сервера: ' + (error instanceof Error ? error.message : String(error)) },
      { status: 500 }
    );
  }
}
