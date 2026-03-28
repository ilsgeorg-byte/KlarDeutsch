/**
 * AI проверка слов - серверная реализация для Vercel
 * Запускает проверку напрямую через Groq API без Python скриптов
 */

import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';
import OpenAI from 'openai';

const POSTGRES_URL = process.env.POSTGRES_URL || '';
const GROQ_API_KEY = process.env.GROQ_API_KEY || '';

// Хранилище статуса проверки
let checkStatus: {
  running: boolean;
  lastRun: Date | null;
  totalChecked: number;
  errorsFound: number;
  translationsAdded: number;
  greetingConstructions: number;
  message: string;
  progress: { current: number; total: number };
} = {
  running: false,
  lastRun: null,
  totalChecked: 0,
  errorsFound: 0,
  translationsAdded: 0,
  greetingConstructions: 0,
  message: 'Ожидание запуска',
  progress: { current: 0, total: 0 },
};

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
    max: 10, // Максимум подключений
    idleTimeoutMillis: 30000, // Таймаут бездействия 30 сек
    connectionTimeoutMillis: 5000, // Таймаут подключения 5 сек
  });
}

// Инициализация Groq клиента
const groqClient = GROQ_API_KEY ? new OpenAI({
  apiKey: GROQ_API_KEY,
  baseURL: 'https://api.groq.com/openai/v1',
  timeout: 30000,
}) : null;

// Паттерны приветствий
const GREETING_PATTERNS = [
  /^guten\s+tag$/i, /^guten\s+abend$/i, /^guten\s+morgen$/i, /^gute\s+nacht$/i,
  /^guten\s+rutsch$/i, /^frohe\s+weihnachten$/i, /^frohe\s+ostern$/i,
  /^herzlichen\s+glückwunsch/i, /^guten\s+appetit$/i, /^auf\s+wiedersehen$/i,
  /^machs?\s+gut$/i, /^bis\s+bald$/i, /^bis\s+morgen$/i, /^bis\s+später$/i,
];

function isGreetingConstruction(de: string): boolean {
  const deLower = de.toLowerCase().trim();
  return GREETING_PATTERNS.some(pattern => pattern.test(deLower));
}

function hasMixedAlphabet(text: string): boolean {
  if (!text) return false;
  for (const word of text.split(' ')) {
    let cyrillicCount = 0;
    let latinCount = 0;
    for (const char of word) {
      if (/[\u0400-\u04FF]/.test(char)) cyrillicCount++;
      else if (/[a-zäöüßÄÖÜ]/i.test(char)) latinCount++;
    }
    if (cyrillicCount > 0 && latinCount > 0) return true;
  }
  return false;
}

const CHECK_PROMPT = `Ты - строгий эксперт по немецкому языку. Проверь слово.

Слово: {de}
Перевод: {ru}
Артикль: {article}
Формы глагола: {verb_forms}

Правила:
1. Прилагательные: артикль пустой, verb_forms пустые
2. Глаголы: артикль пустой, verb_forms: Infinitiv, Praeteritum, Partizip II
3. Существительные: артикль der/die/das, verb_forms пустые
4. Конструкции (Guten Tag и т.д.): помечай как "Конструкция приветствия - удалить"
5. Несколько переводов: добавляй все значимые переводы

Верни ТОЛЬКО JSON:
{
  "word_type": "adjective|verb|noun|phrase",
  "valid": true/false,
  "errors": [],
  "corrected_de": "",
  "corrected_ru": "",
  "corrected_article": "",
  "corrected_verb_forms": "",
  "additional_translations": [],
  "confidence": 0.0-1.0,
  "is_greeting_construction": true/false
}`;

async function checkWordWithAI(de: string, ru: string, article: string, verb_forms: string) {
  // Локальные проверки
  if (hasMixedAlphabet(ru)) {
    return {
      valid: false,
      errors: ['Смешение алфавитов (кириллица + латиница)'],
      corrected_ru: ru,
      confidence: 1.0,
      additional_translations: []
    };
  }

  if (hasMixedAlphabet(de)) {
    return {
      valid: false,
      errors: ['Смешение алфавитов в немецком слове'],
      corrected_de: de,
      confidence: 1.0,
      additional_translations: []
    };
  }

  if (isGreetingConstruction(de)) {
    return {
      valid: false,
      errors: ['Конструкция приветствия - удалить'],
      is_greeting_construction: true,
      confidence: 1.0,
      additional_translations: []
    };
  }

  // Проверка через Groq AI
  if (!groqClient) {
    return { valid: true, errors: [], confidence: 0.5, additional_translations: [] };
  }

  try {
    const prompt = CHECK_PROMPT
      .replace('{de}', de)
      .replace('{ru}', ru)
      .replace('{article}', article || 'пусто')
      .replace('{verb_forms}', verb_forms || 'пусто');

    const response = await groqClient.chat.completions.create({
      model: 'llama-3.3-70b-versatile',
      messages: [
        { role: 'system', content: 'Ты проверяешь немецкие слова. Возвращай ТОЛЬКО JSON, без markdown.' },
        { role: 'user', content: prompt }
      ],
      temperature: 0.1,
      max_tokens: 600,
    });

    let content = response.choices[0]?.message?.content?.trim() || '';
    
    // Убираем markdown
    content = content.replace(/```json/g, '').replace(/```/g, '').trim();
    
    // Извлекаем JSON
    const jsonMatch = content.match(/\{.*\}/s);
    if (jsonMatch) content = jsonMatch[0];

    const result = JSON.parse(content);
    if (!result.additional_translations) result.additional_translations = [];
    
    return result;
  } catch (error) {
    console.error('AI check error:', error);
    return { valid: true, errors: [], confidence: 0.5, additional_translations: [] };
  }
}

async function runWordCheck(limit: number = 500): Promise<void> {
  if (checkStatus.running) return;

  checkStatus.running = true;
  checkStatus.message = 'Запуск проверки...';
  checkStatus.progress = { current: 0, total: 0 };

  let pool = getPool();
  if (!pool) {
    checkStatus.message = 'Ошибка: БД не подключена';
    checkStatus.running = false;
    return;
  }

  try {
    // Получаем слова для проверки
    let result;
    try {
      result = await pool.query(`
        SELECT id, de, ru, article, verb_forms, level
        FROM words
        WHERE ai_checked_at IS NULL
        ORDER BY id
        LIMIT $1
      `, [limit]);
    } catch (dbError: any) {
      console.error('DB query error:', dbError.message);
      // Пробуем переподключиться
      await pool.end().catch(() => {});
      pool = getPool()!;
      result = await pool.query(`
        SELECT id, de, ru, article, verb_forms, level
        FROM words
        WHERE ai_checked_at IS NULL
        ORDER BY id
        LIMIT $1
      `, [limit]);
    }

    const words = result.rows;
    checkStatus.progress.total = words.length;
    checkStatus.progress.current = 0;

    if (words.length === 0) {
      checkStatus.message = 'Нет непроверенных слов';
      checkStatus.running = false;
      return;
    }

    let stats = { total: 0, valid: 0, invalid: 0, translationsAdded: 0, greetings: 0 };

    for (const word of words) {
      try {
        const aiResult = await checkWordWithAI(word.de, word.ru, word.article, word.verb_forms);
        stats.total++;
        checkStatus.progress.current = stats.total;

        if (aiResult.valid) {
          stats.valid++;
          // Добавляем дополнительные переводы если есть
          if (aiResult.additional_translations?.length > 0) {
            const currentRu = word.ru;
            const newTranslations = aiResult.additional_translations.filter(
              (t: string) => !currentRu.toLowerCase().includes(t.toLowerCase())
            );
            if (newTranslations.length > 0) {
              try {
                await pool.query(
                  `UPDATE words SET ru = $1, ai_checked_at = NOW() WHERE id = $2`,
                  [currentRu + ', ' + newTranslations.join(', '), word.id]
                );
                stats.translationsAdded += newTranslations.length;
              } catch (updateError: any) {
                console.error(`Update error for word ${word.id}:`, updateError.message);
                // Пропускаем ошибку обновления
              }
            } else {
              await pool.query(
                `UPDATE words SET ai_checked_at = NOW() WHERE id = $1`,
                [word.id]
              );
            }
          } else {
            await pool.query(
              `UPDATE words SET ai_checked_at = NOW() WHERE id = $1`,
              [word.id]
            );
          }
        } else {
          stats.invalid++;

          if (aiResult.is_greeting_construction) {
            stats.greetings++;
            // Помечаем как проверенное (чтобы не проверять снова)
            try {
              await pool.query(
                `UPDATE words SET ai_checked_at = NOW() WHERE id = $1`,
                [word.id]
              );
            } catch (updateError: any) {
              console.error(`Update error for greeting ${word.id}:`, updateError.message);
            }
            checkStatus.message = `Проверка: ${stats.total}/${words.length}. Найдено конструкций: ${stats.greetings}`;
          } else {
            // Исправляем ошибки
            const newDe = aiResult.corrected_de || word.de;
            const newRu = aiResult.corrected_ru || word.ru;
            const newArticle = aiResult.corrected_article ?? word.article;
            const newVerbForms = aiResult.corrected_verb_forms ?? word.verb_forms;

            try {
              await pool.query(
                `UPDATE words SET de = $1, ru = $2, article = $3, verb_forms = $4, ai_checked_at = NOW() WHERE id = $5`,
                [newDe, newRu, newArticle || '', newVerbForms || '', word.id]
              );
              checkStatus.message = `Проверка: ${stats.total}/${words.length}. Ошибок: ${stats.invalid}`;
            } catch (updateError: any) {
              console.error(`Update error for word ${word.id}:`, updateError.message);
              // Пропускаем ошибку обновления
            }
          }
        }
      } catch (wordError: any) {
        console.error(`Error processing word ${word.id}:`, wordError.message);
        // Продолжаем проверку следующих слов
      }

      // Небольшая задержка чтобы не превысить лимиты API
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    // Сохраняем статистику
    checkStatus.totalChecked = stats.total;
    checkStatus.errorsFound = stats.invalid;
    checkStatus.translationsAdded = stats.translationsAdded;
    checkStatus.greetingConstructions = stats.greetings;
    checkStatus.message = `Проверка завершена. Найдено ошибок: ${stats.invalid}, добавлено переводов: ${stats.translationsAdded}`;
    checkStatus.lastRun = new Date();

  } catch (error) {
    console.error('Word check error:', error);
    checkStatus.message = `Ошибка: ${error instanceof Error ? error.message : String(error)}`;
  } finally {
    checkStatus.running = false;
    await pool.end();
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { limit = 500 } = body || {};

    if (!POSTGRES_URL) {
      return NextResponse.json({ error: 'POSTGRES_URL не настроен' }, { status: 500 });
    }

    if (!GROQ_API_KEY) {
      return NextResponse.json({ error: 'GROQ_API_KEY не настроен' }, { status: 500 });
    }

    if (checkStatus.running) {
      return NextResponse.json({
        status: 'already_running',
        message: 'Проверка уже запущена',
        currentStatus: checkStatus,
      });
    }

    // Запускаем проверку (асинхронно)
    runWordCheck(limit).catch(console.error);

    return NextResponse.json({
      status: 'started',
      message: `Запущена проверка ${limit} слов`,
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
  return NextResponse.json({
    running: checkStatus.running,
    lastRun: checkStatus.lastRun,
    totalChecked: checkStatus.totalChecked,
    errorsFound: checkStatus.errorsFound,
    translationsAdded: checkStatus.translationsAdded,
    greetingConstructions: checkStatus.greetingConstructions,
    message: checkStatus.message,
    progress: checkStatus.progress,
  });
}

export async function DELETE(request: NextRequest) {
  try {
    const body = await request.json();
    const { all = false } = body || {};

    if (!POSTGRES_URL) {
      return NextResponse.json({ error: 'POSTGRES_URL не настроен' }, { status: 500 });
    }

    const pool = getPool();
    if (!pool) {
      return NextResponse.json({ error: 'Не удалось подключиться к БД' }, { status: 500 });
    }

    const result = await pool.query(
      all 
        ? `UPDATE words SET ai_checked_at = NULL`
        : `UPDATE words SET ai_checked_at = NULL WHERE ai_checked_at IS NOT NULL ORDER BY ai_checked_at DESC LIMIT 500`
    );

    const resetCount = result?.rowCount || 0;

    // Сбрасываем статус
    checkStatus.totalChecked = 0;
    checkStatus.errorsFound = 0;
    checkStatus.translationsAdded = 0;
    checkStatus.greetingConstructions = 0;
    checkStatus.message = 'Статус сброшен';
    checkStatus.progress = { current: 0, total: 0 };

    await pool.end();

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
