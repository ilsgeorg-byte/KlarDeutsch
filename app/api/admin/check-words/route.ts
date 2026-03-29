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

const ENRICH_PROMPT = `Ты - эксперт по немецкому языку. Обогати слово данными.

Слово: {de}
Перевод: {ru}
Артикль: {article}
Формы глагола: {verb_forms}
Пример: {example}
Множественное число: {plural}

ЗАДАЧА:
1. Проверь и исправь ошибки (артикль, формы глагола)
2. Если нет примеров - создай МИНИМУМ 3 разных предложения с этим словом + перевод
3. Если нет множественного числа (для существительных) - добавь
4. Найди 2-3 синонима (если есть)
5. Найди 1-2 антонима (если есть)
6. Найди 2-3 коллокации (устойчивые сочетания)

Верни ТОЛЬКО JSON:
{
  "word_type": "noun|verb|adjective|phrase",
  "valid": true/false,
  "errors": [],
  "corrected_de": "",
  "corrected_ru": "",
  "corrected_article": "",
  "corrected_verb_forms": "",
  "additional_translations": [],
  "examples": [
    {"de": "Ich esse einen Apfel.", "ru": "Я ем яблоко."},
    {"de": "Der Apfel ist rot.", "ru": "Яблоко красное."},
    {"de": "Sie kauft einen Apfel.", "ru": "Она покупает яблоко."}
  ],
  "plural": "",
  "synonyms": [],
  "antonyms": [],
  "collocations": [],
  "confidence": 0.0-1.0,
  "is_greeting_construction": true/false
}`;

async function enrichWord(de: string, ru: string, article: string, verb_forms: string, example: string, plural: string) {
  // Локальные проверки
  if (hasMixedAlphabet(ru)) {
    return {
      valid: false,
      errors: ['Смешение алфавитов'],
      corrected_ru: ru,
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
        { role: 'system', content: 'Ты обогащаешь немецкие слова. Возвращай ТОЛЬКО JSON, без markdown.' },
        { role: 'user', content: prompt }
      ],
      temperature: 0.5, // Чуть выше для разнообразия примеров
      max_tokens: 1200, // Больше токенов для 3 примеров
    });

    let content = response.choices[0]?.message?.content?.trim() || '';
    content = content.replace(/```json/g, '').replace(/```/g, '').trim();
    
    const jsonMatch = content.match(/\{.*\}/s);
    if (jsonMatch) content = jsonMatch[0];

    const result = JSON.parse(content);
    
    // Инициализируем пустые массивы
    if (!result.additional_translations) result.additional_translations = [];
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

  const BATCH_SIZE = 20; // Уменьшил до 20 (богаче данные = дольше обработка)
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
        SELECT id, de, ru, article, verb_forms, level, example_de, example_ru, plural, synonyms, antonyms, collocations, examples
        FROM words
        WHERE ai_checked_at IS NULL
        ORDER BY id
        LIMIT $1
      `, [BATCH_SIZE]);

      const words = result.rows;
      
      if (words.length === 0) {
        emptyBatchCount++;
        if (emptyBatchCount >= MAX_EMPTY_BATCHES) {
          checkStatus.message = `Нет непроверенных слов. Проверено: ${processedCount} из ${limit}`;
          shouldStop = true;
        } else {
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
        await pool.end().catch(() => {});
        continue;
      }

      emptyBatchCount = 0;
      console.log(`[check-words] Batch ${Math.floor(processedCount/BATCH_SIZE)+1}: ${words.length} words`);
      
      let batchStats = { 
        total: 0, valid: 0, invalid: 0, 
        translationsAdded: 0, examplesAdded: 0, pluralAdded: 0,
        synonymsAdded: 0, antonymsAdded: 0, collocationsAdded: 0,
        greetings: 0 
      };

      for (const word of words) {
        if (shouldStop || processedCount >= limit) break;

        try {
          const aiResult = await enrichWord(
            word.de, word.ru, word.article, word.verb_forms,
            word.example_de || '', word.plural || ''
          );
          
          batchStats.total++;
          processedCount++;
          checkStatus.progress.current = processedCount;

          if (aiResult.valid) {
            batchStats.valid++;
            
            // Собираем все обновления
            const updates: any = {};
            
            // Дополнительные переводы
            if (aiResult.additional_translations?.length > 0) {
              const currentRu = word.ru;
              const newTranslations = aiResult.additional_translations.filter(
                (t: string) => !currentRu.toLowerCase().includes(t.toLowerCase())
              );
              if (newTranslations.length > 0) {
                updates.ru = currentRu + ', ' + newTranslations.join(', ');
                batchStats.translationsAdded += newTranslations.length;
              }
            }
            
            // Примеры (только если пусто)
            if (!word.example_de && aiResult.examples?.length > 0) {
              // Берём первый пример для полей example_de/example_ru
              updates.example_de = aiResult.examples[0].de;
              updates.example_ru = aiResult.examples[0].ru || '';
              
              // Если примеров больше 1, сохраняем все в JSONB поле examples
              if (aiResult.examples.length > 1) {
                updates.examples = JSON.stringify(aiResult.examples);
              }
              
              batchStats.examplesAdded += aiResult.examples.length;
            }
            
            // Множественное число (только если пусто)
            if (!word.plural && aiResult.plural) {
              updates.plural = aiResult.plural;
              batchStats.pluralAdded++;
            }
            
            // Синонимы (только если пусто)
            if (!word.synonyms && aiResult.synonyms?.length > 0) {
              updates.synonyms = aiResult.synonyms.join(', ');
              batchStats.synonymsAdded += aiResult.synonyms.length;
            }
            
            // Антонимы (только если пусто)
            if (!word.antonyms && aiResult.antonyms?.length > 0) {
              updates.antonyms = aiResult.antonyms.join(', ');
              batchStats.antonymsAdded += aiResult.antonyms.length;
            }
            
            // Коллокации (только если пусто)
            if (!word.collocations && aiResult.collocations?.length > 0) {
              updates.collocations = aiResult.collocations.join(', ');
              batchStats.collocationsAdded += aiResult.collocations.length;
            }
            
            // Исправления
            if (aiResult.corrected_de && aiResult.corrected_de !== word.de) updates.de = aiResult.corrected_de;
            if (aiResult.corrected_ru && aiResult.corrected_ru !== word.ru) updates.ru = aiResult.corrected_ru;
            if (aiResult.corrected_article && aiResult.corrected_article !== word.article) updates.article = aiResult.corrected_article;
            if (aiResult.corrected_verb_forms && aiResult.corrected_verb_forms !== word.verb_forms) updates.verb_forms = aiResult.corrected_verb_forms;
            
            // Обновляем если есть изменения
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
            batchStats.invalid++;
            
            if (aiResult.is_greeting_construction) {
              batchStats.greetings++;
              await pool.query(`UPDATE words SET ai_checked_at = NOW() WHERE id = $1`, [word.id]);
              checkStatus.message = `Проверка: ${processedCount}/${limit}. Конструкций: ${batchStats.greetings}`;
            } else {
              // Исправляем ошибки
              const updates: any = {};
              if (aiResult.corrected_de) updates.de = aiResult.corrected_de;
              if (aiResult.corrected_ru) updates.ru = aiResult.corrected_ru;
              if (aiResult.corrected_article) updates.article = aiResult.corrected_article;
              if (aiResult.corrected_verb_forms) updates.verb_forms = aiResult.corrected_verb_forms;
              
              if (Object.keys(updates).length > 0) {
                const fields = Object.keys(updates).map((f, i) => `${f} = $${i + 1}`).join(', ');
                const values = Object.values(updates);
                await pool.query(
                  `UPDATE words SET ${fields}, ai_checked_at = NOW() WHERE id = $${Object.keys(updates).length + 1}`,
                  [...values, word.id]
                );
              }
              checkStatus.message = `Проверка: ${processedCount}/${limit}. Ошибок: ${batchStats.invalid}`;
            }
          }
        } catch (wordError: any) {
          console.error(`Error word ${word.id}:`, wordError.message);
          processedCount++;
        }

        await new Promise(resolve => setTimeout(resolve, 500)); // 500мс на слово (богаче обработка)
      }

      checkStatus.totalChecked = processedCount;
      checkStatus.errorsFound = checkStatus.errorsFound + batchStats.invalid;
      checkStatus.translationsAdded = checkStatus.translationsAdded + batchStats.translationsAdded;
      checkStatus.examplesAdded = checkStatus.examplesAdded + batchStats.examplesAdded;
      checkStatus.pluralAdded = checkStatus.pluralAdded + batchStats.pluralAdded;
      checkStatus.synonymsAdded = checkStatus.synonymsAdded + batchStats.synonymsAdded;
      checkStatus.antonymsAdded = checkStatus.antonymsAdded + batchStats.antonymsAdded;
      checkStatus.collocationsAdded = checkStatus.collocationsAdded + batchStats.collocationsAdded;
      checkStatus.greetingConstructions = checkStatus.greetingConstructions + batchStats.greetings;

      console.log(`[check-words] Batch done: ${processedCount}/${limit}`);
      await pool.end().catch(() => {});
      
      if (!shouldStop && processedCount < limit) {
        await new Promise(resolve => setTimeout(resolve, 2000));
      }

    } catch (error: any) {
      console.error('Batch error:', error.message);
      await pool.end().catch(() => {});
      
      if (error.message.includes('timeout') || error.message.includes('terminated') || error.message.includes('ECONNRESET')) {
        console.log(`[check-words] Connection error, retrying...`);
        await new Promise(resolve => setTimeout(resolve, 2000));
      } else {
        checkStatus.message = `Ошибка: ${error.message}`;
        checkStatus.running = false;
        return;
      }
    }
  }

  checkStatus.message = `Готово! Проверено: ${processedCount} из ${limit}
    Ошибок: ${checkStatus.errorsFound}
    Переводов: +${checkStatus.translationsAdded}
    Примеров: +${checkStatus.examplesAdded}
    Множественное число: +${checkStatus.pluralAdded}
    Синонимы: +${checkStatus.synonymsAdded}
    Антонимы: +${checkStatus.antonymsAdded}
    Коллокации: +${checkStatus.collocationsAdded}
    Конструкций: ${checkStatus.greetingConstructions}`;
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
