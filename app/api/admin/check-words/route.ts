/**
 * AI проверка и обогащение слов (Синхронная версия для итеративной работы)
 */

import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';
import OpenAI from 'openai';

const POSTGRES_URL = process.env.POSTGRES_URL || '';
const GROQ_API_KEY = process.env.GROQ_API_KEY || '';

// Глобальный статус для GET запросов (опционально, для совместимости)
let globalCheckStatus = {
  lastRun: new Date(),
  totalChecked: 0,
  errorsFound: 0,
  translationsAdded: 0,
  examplesAdded: 0,
  pluralAdded: 0,
  synonymsAdded: 0,
  antonymsAdded: 0,
  collocationsAdded: 0,
  greetingConstructions: 0,
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
    max: 1, // Для одного запроса достаточно 1 соединения
    connectionTimeoutMillis: 10000,
  });
}

const groqClient = GROQ_API_KEY ? new OpenAI({
  apiKey: GROQ_API_KEY,
  baseURL: 'https://api.groq.com/openai/v1',
  timeout: 45000, // Увеличиваем таймаут для LLM
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
  if (isGreetingConstruction(de)) {
    return { valid: false, errors: ['Конструкция приветствия'], is_greeting_construction: true };
  }

  if (!groqClient) return { valid: true, errors: [], confidence: 0.5 };

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

    const result = JSON.parse(response.choices[0]?.message?.content?.trim() || '{}');
    if (!result.examples) result.examples = [];
    return result;
  } catch (error) {
    console.error('AI enrich error:', error);
    return { valid: true, errors: [], confidence: 0.5 };
  }
}

export async function POST(request: NextRequest) {
  const pool = getPool();
  if (!pool) return NextResponse.json({ error: 'DB not connected' }, { status: 500 });

  try {
    const body = await request.json();
    const { batchSize = 5 } = body; // Обрабатываем по 5 слов за раз

    const result = await pool.query(`
      SELECT id, de, ru, article, verb_forms, level, topic, example_de, example_ru, plural, synonyms, antonyms, collocations, examples
      FROM words
      WHERE ai_checked_at IS NULL
      ORDER BY id
      LIMIT $1
    `, [batchSize]);

    const words = result.rows;
    const stats = {
      checked: 0,
      errors: 0,
      translations: 0,
      examples: 0,
      plural: 0,
      synonyms: 0,
      antonyms: 0,
      collocations: 0,
      greetings: 0
    };

    for (const word of words) {
      try {
        const aiResult = await enrichWord(
          word.de, word.ru, word.article, word.verb_forms,
          word.example_de || '', word.plural || ''
        );
        
        stats.checked++;
        const updates: any = {};

        if (aiResult.is_greeting_construction) {
          stats.greetings++;
          // Помечаем как проверенное, но фронтенд может их удалить
          await pool.query(`UPDATE words SET ai_checked_at = NOW() WHERE id = $1`, [word.id]);
          continue;
        }

        if (aiResult.valid) {
          if (aiResult.ru && aiResult.ru !== word.ru) { updates.ru = aiResult.ru; stats.translations++; }
          if (aiResult.topic && (!word.topic || word.topic === 'Общее')) updates.topic = aiResult.topic;
          
          if (!word.example_de && aiResult.examples?.length > 0) {
            updates.example_de = aiResult.examples[0].de;
            updates.example_ru = aiResult.examples[0].ru || '';
            updates.examples = JSON.stringify(aiResult.examples);
            stats.examples += aiResult.examples.length;
          }
          
          if (aiResult.corrected_plural && aiResult.corrected_plural !== word.plural) {
            updates.plural = aiResult.corrected_plural;
            stats.plural++;
          }

          if (!word.synonyms && aiResult.synonyms?.length > 0) {
            updates.synonyms = aiResult.synonyms.join(', ');
            stats.synonyms += aiResult.synonyms.length;
          }

          if (Object.keys(updates).length > 0) {
            const fields = Object.keys(updates).map((f, i) => `${f} = $${i + 1}`).join(', ');
            const values = Object.values(updates);
            await pool.query(`UPDATE words SET ${fields}, ai_checked_at = NOW() WHERE id = $${values.length + 1}`, [...values, word.id]);
          } else {
            await pool.query(`UPDATE words SET ai_checked_at = NOW() WHERE id = $1`, [word.id]);
          }
        } else {
          stats.errors++;
          await pool.query(`UPDATE words SET ai_checked_at = NOW() WHERE id = $1`, [word.id]);
        }
      } catch (e) {
        console.error(`Word ${word.id} error:`, e);
      }
    }

    await pool.end();
    return NextResponse.json({ success: true, stats, remaining: words.length === batchSize });

  } catch (error: any) {
    await pool.end();
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

export async function GET() {
  const pool = getPool();
  if (!pool) return NextResponse.json({ error: 'DB not connected' }, { status: 500 });

  try {
    const result = await pool.query(`SELECT COUNT(*) FROM words WHERE ai_checked_at IS NOT NULL`);
    const totalCheckedInDb = parseInt(result.rows[0]?.count || '0');
    
    const remainingResult = await pool.query(`SELECT COUNT(*) FROM words WHERE ai_checked_at IS NULL`);
    const totalRemainingInDb = parseInt(remainingResult.rows[0]?.count || '0');

    await pool.end();
    return NextResponse.json({
      running: false, // Теперь фронтенд управляет состоянием
      totalCheckedInDb,
      totalRemainingInDb,
      message: totalRemainingInDb > 0 ? `Осталось проверить: ${totalRemainingInDb}` : 'Все слова проверены'
    });
  } catch (error) {
    await pool.end();
    return NextResponse.json({ error: 'Server error' }, { status: 500 });
  }
}

export async function DELETE(request: NextRequest) {
  const pool = getPool();
  if (!pool) return NextResponse.json({ error: 'DB not connected' }, { status: 500 });

  try {
    const body = await request.json();
    const { all = false } = body;
    const query = all 
      ? `UPDATE words SET ai_checked_at = NULL` 
      : `UPDATE words SET ai_checked_at = NULL WHERE id IN (SELECT id FROM words WHERE ai_checked_at IS NOT NULL ORDER BY ai_checked_at DESC LIMIT 500)`;
    
    const result = await pool.query(query);
    await pool.end();
    return NextResponse.json({ success: true, resetCount: result.rowCount });
  } catch (error: any) {
    await pool.end();
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
