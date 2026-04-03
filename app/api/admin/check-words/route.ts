/**
 * AI проверка и обогащение слов
 * - Проверка ошибок (артикль, формы, смешение алфавитов)
 * - Добавление примеров, множественного числа, синонимов, антонимов, коллокаций
 * - Удаление конструкций приветствий
 */

import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';
import OpenAI from 'openai';

const POSTGRES_URL = process.env.POSTGRES_URL || '';
const GROQ_API_KEY = process.env.GROQ_API_KEY || '';

let checkStatus: {
  running: boolean;
  lastRun: Date | null;
  totalChecked: number;
  errorsFound: number;
  translationsAdded: number;
  examplesAdded: number;
  pluralAdded: number;
  synonymsAdded: number;
  antonymsAdded: number;
  collocationsAdded: number;
  greetingConstructions: number;
  message: string;
  progress: { current: number; total: number };
} = {
  running: false,
  lastRun: null,
  totalChecked: 0,
  errorsFound: 0,
  translationsAdded: 0,
  examplesAdded: 0,
  pluralAdded: 0,
  synonymsAdded: 0,
  antonymsAdded: 0,
  collocationsAdded: 0,
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
    max: 20,
    idleTimeoutMillis: 120000,
    connectionTimeoutMillis: 15000,
    keepAlive: true,
    statement_timeout: 60000,
    query_timeout: 60000,
  });
}

const groqClient = GROQ_API_KEY ? new OpenAI({
  apiKey: GROQ_API_KEY,
  baseURL: 'https://api.groq.com/openai/v1',
  timeout: 30000,
}) : null;

const GREETING_PATTERNS = [
  /^guten\s+tag$/i, /^guten\s+abend$/i, /^guten\s+morgen$/i, /^gute\s+nacht$/i,
  /^guten\s+rutsch$/i, /^frohe\s+weihnachten$/i, /^frohe\s+ostern$/i,
  /^herzlichen\s+glückwunsch/i, /^guten\s+appetit$/i, /^auf\s+wiedersehen$/i,
  /^machs?\s+gut$/i, /^bis\s+bald$/i, /^bis\s+morgen$/i, /^bis\s+später$/i,
];

function isGreetingConstruction(de: string): boolean {
  return GREETING_PATTERNS.some(pattern => pattern.test(de.toLowerCase().trim()));
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

const ENRICH_PROMPT = `Ты - эксперт по немецкому языку. Обогати слово данными для учебного приложения.

Слово: {de}
Текущий перевод: {ru}
Артикль: {article}
Формы глагола: {verb_forms}
Пример: {example}
Множественное число: {plural}

ЗАДАЧА:
1. Проверь и исправь ошибки.
2. ПЕРЕВОД (ru): Дай точный перевод.
3. ТЕМА (topic): Определи тему.
4. ГЛАГОЛЫ И ПРИЛАГАТЕЛЬНЫЕ: Поля "corrected_article" и "corrected_plural" ОБЯЗАТЕЛЬНО должны быть пустой строкой ("").
5. СУЩЕСТВИТЕЛЬНЫЕ: Артикль (der/die/das) и Plural обязательны.
6. ПРИМЕРЫ (examples): Создай МИНИМУМ 3 предложения с переводом.
7. СИНОНИМЫ/АНТОНИМЫ/КОЛЛОКАЦИИ: Найди по 2-3 наиболее употребимых.

Верни ТОЛЬКО JSON:
{
  "word_type": "noun|verb|adjective|phrase",
  "valid": true,
  "errors": [],
  "corrected_de": "",
  "ru": "перевод",
  "topic": "Тема",
  "corrected_article": "",
  "corrected_plural": "",
  "corrected_verb_forms": "forms (только для глаголов)",
  "examples": [
    {"de": "...", "ru": "..."},
    {"de": "...", "ru": "..."},
    {"de": "...", "ru": "..."}
  ],
  "synonyms": ["син1", "син2"],
  "antonyms": ["ант1", "ант2"],
  "collocations": ["колл1", "колл2", "колл3"],
  "confidence": 1.0,
  "is_greeting_construction": false
}`;

async function enrichWord(de: string, ru: string, article: string, verb_forms: string, example: string, plural: string) {
  // Локальные проверки
  if (hasMixedAlphabet(ru)) {
    return {
      valid: false,
      errors: ['Смешение алфавитов'],
      ru: ru,
      confidence: 1.0,
    };
  }

  if (hasMixedAlphabet(de)) {
    return {
      valid: false,
      errors: ['Смешение алфавитов в немецком'],
      corrected_de: de,
      confidence: 1.0,
    };
  }

  if (isGreetingConstruction(de)) {
    return {
      valid: false,
      errors: ['Конструкция приветствия - удалить'],
      is_greeting_construction: true,
      confidence: 1.0,
    };
  }

  if (!groqClient) {
    return { valid: true, errors: [], confidence: 0.5 };
  }

  try {
    const prompt = ENRICH_PROMPT
      .replace('{de}', de)
      .replace('{ru}', ru)
      .replace('{article}', article || 'пусто')
      .replace('{verb_forms}', verb_forms || 'пусто')
      .replace('{example}', example || 'пусто')
      .replace('{plural}', plural || 'пусто');

    const response = await groqClient.chat.completions.create({
      model: 'llama-3.3-70b-versatile',
      messages: [
        { role: 'system', content: 'Ты - лингвистический эксперт. Возвращай только валидный JSON.' },
        { role: 'user', content: prompt }
      ],
      temperature: 0.2, 
      max_tokens: 1500,
      response_format: { type: "json_object" }
    });

    let content = response.choices[0]?.message?.content?.trim() || '';
    const result = JSON.parse(content);
    
    // Инициализируем пустые массивы и поля
    if (!result.examples) result.examples = [];
    if (!result.synonyms) result.synonyms = [];
    if (!result.antonyms) result.antonyms = [];
    if (!result.collocations) result.collocations = [];
    
    return result;
  } catch (error) {
    console.error('AI enrich error:', error);
    return { valid: true, errors: [], confidence: 0.5 };
  }
}

async function runWordCheck(limit: number = 500): Promise<void> {
  if (checkStatus.running) return;

  checkStatus.running = true;
  checkStatus.message = 'Запуск проверки и обогащения...';
  checkStatus.progress = { current: 0, total: limit };
  checkStatus.totalChecked = 0;
  checkStatus.errorsFound = 0;
  checkStatus.translationsAdded = 0;
  checkStatus.examplesAdded = 0;
  checkStatus.pluralAdded = 0;
  checkStatus.synonymsAdded = 0;
  checkStatus.antonymsAdded = 0;
  checkStatus.collocationsAdded = 0;
  checkStatus.greetingConstructions = 0;

  const BATCH_SIZE = 10; // Еще меньше, так как данных много
  let processedCount = 0;
  let shouldStop = false;
  let emptyBatchCount = 0;
  const MAX_EMPTY_BATCHES = 3;

  while (!shouldStop && processedCount < limit) {
    let pool = getPool();
    if (!pool) {
      checkStatus.message = 'Ошибка: БД не подключена';
      checkStatus.running = false;
      return;
    }

    try {
      const result = await pool.query(`
        SELECT id, de, ru, article, verb_forms, level, topic, example_de, example_ru, plural, synonyms, antonyms, collocations, examples
        FROM words
        WHERE ai_checked_at IS NULL
        ORDER BY id
        LIMIT $1
      `, [BATCH_SIZE]);

      const words = result.rows;
      
      if (words.length === 0) {
        emptyBatchCount++;
        if (emptyBatchCount >= MAX_EMPTY_BATCHES) {
          checkStatus.message = `Нет непроверенных слов. Проверено: ${processedCount}`;
          shouldStop = true;
        } else {
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
        await pool.end().catch(() => {});
        continue;
      }

      emptyBatchCount = 0;
      
      for (const word of words) {
        if (shouldStop || processedCount >= limit) break;

        try {
          const aiResult = await enrichWord(
            word.de, word.ru, word.article, word.verb_forms,
            word.example_de || '', word.plural || ''
          );
          
          processedCount++;
          checkStatus.progress.current = processedCount;

          if (aiResult.valid) {
            // Собираем все обновления
            const updates: any = {};
            
            // Перевод (обогащаем если ИИ дал больше значений)
            if (aiResult.ru && aiResult.ru !== word.ru) {
              updates.ru = aiResult.ru;
              checkStatus.translationsAdded++;
            }
            
            // Тема
            if (aiResult.topic && (!word.topic || word.topic === 'Общее' || word.topic === 'Личные слова')) {
              updates.topic = aiResult.topic;
            }

            // Примеры (только если пусто)
            if (!word.example_de && aiResult.examples?.length > 0) {
              updates.example_de = aiResult.examples[0].de;
              updates.example_ru = aiResult.examples[0].ru || '';
              updates.examples = JSON.stringify(aiResult.examples);
              checkStatus.examplesAdded += aiResult.examples.length;
            }
            
            // Множественное число
            if (aiResult.corrected_plural && aiResult.corrected_plural !== word.plural) {
              updates.plural = aiResult.corrected_plural;
              checkStatus.pluralAdded++;
            }
            
            // Синонимы
            if (!word.synonyms && aiResult.synonyms?.length > 0) {
              updates.synonyms = aiResult.synonyms.join(', ');
              checkStatus.synonymsAdded += aiResult.synonyms.length;
            }
            
            // Антонимы
            if (!word.antonyms && aiResult.antonyms?.length > 0) {
              updates.antonyms = aiResult.antonyms.join(', ');
              checkStatus.antonymsAdded += aiResult.antonyms.length;
            }
            
            // Коллокации
            if (!word.collocations && aiResult.collocations?.length > 0) {
              updates.collocations = aiResult.collocations.join(', ');
              checkStatus.collocationsAdded += aiResult.collocations.length;
            }
            
            // Исправления
            if (aiResult.corrected_de && aiResult.corrected_de !== word.de) updates.de = aiResult.corrected_de;
            if (aiResult.corrected_article && aiResult.corrected_article !== word.article) updates.article = aiResult.corrected_article;
            if (aiResult.corrected_verb_forms && aiResult.corrected_verb_forms !== word.verb_forms) updates.verb_forms = aiResult.corrected_verb_forms;
            
            if (Object.keys(updates).length > 0) {
              const fields = Object.keys(updates).map((f, i) => `${f} = $${i + 1}`).join(', ');
              const values = Object.values(updates);
              await pool.query(
                `UPDATE words SET ${fields}, ai_checked_at = NOW() WHERE id = $${Object.keys(updates).length + 1}`,
                [...values, word.id]
              );
            } else {
              await pool.query(`UPDATE words SET ai_checked_at = NOW() WHERE id = $1`, [word.id]);
            }
            
          } else {
            if (aiResult.is_greeting_construction) {
              checkStatus.greetingConstructions++;
              await pool.query(`UPDATE words SET ai_checked_at = NOW() WHERE id = $1`, [word.id]);
            } else {
              checkStatus.errorsFound++;
              // Принудительно сохраняем исправления даже если не "valid" в лингвистическом смысле
              const updates: any = {};
              if (aiResult.corrected_de) updates.de = aiResult.corrected_de;
              if (aiResult.ru) updates.ru = aiResult.ru;
              if (aiResult.corrected_article) updates.article = aiResult.corrected_article;
              
              if (Object.keys(updates).length > 0) {
                const fields = Object.keys(updates).map((f, i) => `${f} = $${i + 1}`).join(', ');
                const values = Object.values(updates);
                await pool.query(`UPDATE words SET ${fields}, ai_checked_at = NOW() WHERE id = $${values.length + 1}`, [...values, word.id]);
              } else {
                await pool.query(`UPDATE words SET ai_checked_at = NOW() WHERE id = $1`, [word.id]);
              }
            }
          }
        } catch (wordError: any) {
          console.error(`Error word ${word.id}:`, wordError.message);
          processedCount++;
        }

        await new Promise(resolve => setTimeout(resolve, 800));
      }

      console.log(`[check-words] Batch done: ${processedCount}/${limit}`);
      await pool.end().catch(() => {});
      
      if (!shouldStop && processedCount < limit) {
        await new Promise(resolve => setTimeout(resolve, 1500));
      }

    } catch (error: any) {
      console.error('Batch error:', error.message);
      await pool.end().catch(() => {});
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }

  checkStatus.message = 'Проверка завершена';
  checkStatus.lastRun = new Date();
  checkStatus.running = false;
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
  try {
    // Получаем общее количество проверенных слов из БД
    let totalCheckedInDb = 0;
    try {
      const pool = getPool();
      if (pool) {
        const result = await pool.query(`
          SELECT COUNT(*) FROM words WHERE ai_checked_at IS NOT NULL
        `);
        totalCheckedInDb = parseInt(result.rows[0]?.count || '0');
        await pool.end().catch(() => {});
      }
    } catch (e) {
      console.error('Error getting total checked:', e);
    }

    return NextResponse.json({
      running: checkStatus.running,
      lastRun: checkStatus.lastRun,
      totalChecked: checkStatus.totalChecked,
      totalCheckedInDb, // ← Общее количество в базе
      errorsFound: checkStatus.errorsFound,
      translationsAdded: checkStatus.translationsAdded,
      examplesAdded: checkStatus.examplesAdded,
      pluralAdded: checkStatus.pluralAdded,
      synonymsAdded: checkStatus.synonymsAdded,
      antonymsAdded: checkStatus.antonymsAdded,
      collocationsAdded: checkStatus.collocationsAdded,
      greetingConstructions: checkStatus.greetingConstructions,
      message: checkStatus.message,
      progress: checkStatus.progress,
    });
  } catch (error) {
    console.error('Check words status error:', error);
    return NextResponse.json(
      { error: 'Ошибка сервера' },
      { status: 500 }
    );
  }
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
    checkStatus.examplesAdded = 0;
    checkStatus.pluralAdded = 0;
    checkStatus.synonymsAdded = 0;
    checkStatus.antonymsAdded = 0;
    checkStatus.collocationsAdded = 0;
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
