/**
 * AI проверка и обогащение слов (Синхронная версия для итеративной работы)
 */

import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';
import OpenAI from 'openai';

export const dynamic = 'force-dynamic';

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

// Глобальный пул (переиспользуется между запросами)
let _pool: Pool | null = null;

function getPool() {
  if (!_pool && POSTGRES_URL) {
    const isNeon = POSTGRES_URL.includes('neon') || POSTGRES_URL.includes('supabase');
    let connectionString = POSTGRES_URL;
    if (!connectionString.includes('sslmode=')) {
      const separator = connectionString.includes('?') ? '&' : '?';
      connectionString = `${connectionString}${separator}sslmode=verify-full`;
    }

    _pool = new Pool({
      connectionString,
      ssl: isNeon ? { rejectUnauthorized: false } : undefined,
      max: 5,
      connectionTimeoutMillis: 10000,
    });
  }
  return _pool;
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
1. Определи тип слова (noun/verb/adjective/phrase)
2. Проверь и исправь ошибки.
3. ПЕРЕВОД (ru): Дай точный перевод.
4. ТЕМА (topic): Определи тему.
5. СУЩЕСТВИТЕЛЬНЫЕ (word_type = "noun"):
   - corrected_article: ОБЯЗАТЕЛЬНО укажи артикль (der/die/das), даже если он уже есть в поле article
   - corrected_plural: ОБЯЗАТЕЛЬНО укажи форму множественного числа. Если слово не имеет множественного числа, верни "-" (дефис).
   - Примеры: die Unterschrift -> die Unterschriften, das Geld -> - (нет множественного числа)
   - corrected_verb_forms: ОБЯЗАТЕЛЬНО пустая строка ""
6. ГЛАГОЛЫ (word_type = "verb"):
   - corrected_verb_forms: ОБЯЗАТЕЛЬНО укажи 4 формы через запятую: "Infinitiv, Präsens(3sg), Präteritum(3sg), Partizip II"
   - Примеры: gehen -> "gehen, geht, ging, ist gegangen", essen -> "essen, isst, aß, hat gegessen"
   - corrected_article и corrected_plural: ОБЯЗАТЕЛЬНО пустые строки ""
7. ПРИЛАГАТЕЛЬНЫЕ (word_type = "adjective"):
   - corrected_article, corrected_plural, corrected_verb_forms: ОБЯЗАТЕЛЬНО пустые строки ""
   - Примеры: groß (большой), neu (новый), schnell (быстрый)
8. ПРИМЕРЫ (examples): Создай МИНИМУМ 3 предложения с переводом.
9. СИНОНИМЫ/АНТОНИМЫ/КОЛЛОКАЦИИ: Найди по 2-3 наиболее употребимых.

Верни ТОЛЬКО JSON:
{{
  "word_type": "noun|verb|adjective|phrase",
  "valid": true,
  "errors": [],
  "corrected_de": "",
  "ru": "перевод",
  "topic": "Тема",
  "corrected_article": "der/die/das для существительных, иначе пустая строка",
  "corrected_plural": "форма множественного числа или - если нет, иначе пустая строка",
  "corrected_verb_forms": "Infinitiv, Präsens, Präteritum, Partizip II для глаголов, иначе пустая строка",
  "examples": [
    {{"de": "...", "ru": "..."}},
    {{"de": "...", "ru": "..."}},
    {{"de": "...", "ru": "..."}}
  ],
  "synonyms": ["син1", "син2"],
  "antonyms": ["ант1", "ант2"],
  "collocations": ["колл1", "колл2", "колл3"],
  "confidence": 1.0,
  "is_greeting_construction": false
}}`;

async function enrichWord(de: string, ru: string, article: string, verb_forms: string, example: string, plural: string) {
  if (isGreetingConstruction(de)) {
    return { valid: false, errors: ['Конструкция приветствия'], is_greeting_construction: true };
  }

  if (!groqClient) return { valid: false, errors: ['Groq client not configured'], confidence: 0 };

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
      temperature: 0.1, // Снижаем температуру для большей стабильности
      max_tokens: 1500,
      response_format: { type: "json_object" }
    });

    const content = response.choices[0]?.message?.content?.trim() || '{}';
    const result = JSON.parse(content);
    
    // Минимальная валидация
    if (!result.word_type) {
        return { valid: false, errors: ['Missing word_type in AI response'] };
    }

    if (!result.examples) result.examples = [];
    return { ...result, valid: true }; // Явно устанавливаем valid: true если распарсили
  } catch (error) {
    console.error('AI enrich error:', error);
    return { valid: false, errors: [error instanceof Error ? error.message : 'Unknown error'], confidence: 0 };
  }
}

export async function POST(request: NextRequest) {
  const pool = getPool();
  if (!pool) return NextResponse.json({ error: 'DB not connected' }, { status: 500 });

  try {
    const body = await request.json();
    const { batchSize = 5 } = body; 

    // Выбираем слова: либо еще не проверенные, либо проверенные до сегодня с пропущенными формами
    const result = await pool.query(`
      SELECT id, de, ru, article, verb_forms, level, topic, example_de, example_ru, plural, synonyms, antonyms, collocations, examples
      FROM words
      WHERE 
        ai_checked_at IS NULL 
        OR (
          ai_checked_at < '2026-04-04' AND (
            (de ~* '^(der|die|das) ' AND (plural IS NULL OR plural = '' OR plural = '—' OR plural = '-')) OR
            ((article IS NULL OR article = '') AND (verb_forms IS NULL OR verb_forms = '' OR (LENGTH(verb_forms) - LENGTH(REPLACE(verb_forms, ',', ''))) < 3) AND de !~ ' ' AND length(de) > 2 AND length(ru) > 2)
          )
        )
      ORDER BY ai_checked_at NULLS FIRST, id
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
        
        if (aiResult.valid) {
          stats.checked++;
          const updates: any = {};

          if (aiResult.is_greeting_construction) {
            stats.greetings++;
            await pool.query(`UPDATE words SET ai_checked_at = NOW() WHERE id = $1`, [word.id]);
            continue;
          }

          if (aiResult.ru && aiResult.ru !== word.ru) { updates.ru = aiResult.ru; stats.translations++; }
          if (aiResult.topic && (!word.topic || word.topic === 'Общее')) updates.topic = aiResult.topic;

          // Для существительных: добавляем/исправляем артикль и множественное число
          if (aiResult.word_type === 'noun') {
            if (aiResult.corrected_article && aiResult.corrected_article !== word.article) {
              updates.article = aiResult.corrected_article;
            }
            if (aiResult.corrected_plural) {
              const pluralValue = aiResult.corrected_plural.trim();
              if (!word.plural || word.plural.trim() === '' || word.plural === '—' || word.plural === '-' || (pluralValue !== word.plural && pluralValue !== '—')) {
                updates.plural = pluralValue;
                stats.plural++;
              }
            }
          }

          // Для глаголов: добавляем/исправляем формы
          if (aiResult.word_type === 'verb' && aiResult.corrected_verb_forms) {
            if (!word.verb_forms || word.verb_forms.trim() === '' || aiResult.corrected_verb_forms !== word.verb_forms) {
              updates.verb_forms = aiResult.corrected_verb_forms;
            }
          }

          if (!word.example_de && aiResult.examples?.length > 0) {
            updates.example_de = aiResult.examples[0].de;
            updates.example_ru = aiResult.examples[0].ru || '';
            updates.examples = JSON.stringify(aiResult.examples);
            stats.examples += aiResult.examples.length;
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
          // НЕ устанавливаем ai_checked_at если ошибка AI, чтобы попробовать еще раз
          console.error(`Word ${word.id} enrichment failed: `, aiResult.errors);
        }
      } catch (e) {
        console.error(`Word ${word.id} processing error:`, e);
      }
    }

    // Получаем общее число проверенных слов в базе (настоящих)
    const totalCheckedResult = await pool.query(`SELECT COUNT(*) FROM words WHERE ai_checked_at IS NOT NULL`);
    const totalCheckedInDb = parseInt(totalCheckedResult.rows[0]?.count || '0');

    return NextResponse.json({ success: true, stats, remaining: words.length === batchSize, totalCheckedInDb });

  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

export async function GET() {
  const pool = getPool();
  if (!pool) return NextResponse.json({ error: 'DB not connected' }, { status: 500 });

  try {
    const result = await pool.query(`SELECT COUNT(*) FROM words WHERE ai_checked_at IS NOT NULL`);
    const totalCheckedInDb = parseInt(result.rows[0]?.count || '0');

    const remainingResult = await pool.query(`
      SELECT COUNT(*) FROM words 
      WHERE ai_checked_at IS NULL 
      OR (
          ai_checked_at < '2026-04-04' AND (
            (de ~* '^(der|die|das) ' AND (plural IS NULL OR plural = '' OR plural = '—' OR plural = '-')) OR
            ((article IS NULL OR article = '') AND (verb_forms IS NULL OR verb_forms = '' OR (LENGTH(verb_forms) - LENGTH(REPLACE(verb_forms, ',', ''))) < 3) AND de !~ ' ' AND length(de) > 2 AND length(ru) > 2)
          )
        )
    `);

    const totalRemainingInDb = parseInt(remainingResult.rows[0]?.count || '0');

    return NextResponse.json({
      running: false,
      totalCheckedInDb,
      totalRemainingInDb,
      message: totalRemainingInDb > 0 ? `Осталось проверить/исправить: ${totalRemainingInDb}` : 'Все слова проверены'
    });
  } catch (error) {
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

    await pool.query(query);

    // Возвращаем обновлённую статистику
    const remainingResult = await pool.query(`SELECT COUNT(*) FROM words WHERE ai_checked_at IS NULL`);
    const totalRemainingInDb = parseInt(remainingResult.rows[0]?.count || '0');

    return NextResponse.json({
      running: false,
      totalCheckedInDb: 0,
      totalRemainingInDb,
      message: totalRemainingInDb > 0 ? `Осталось проверить: ${totalRemainingInDb}` : 'Все слова проверены'
    });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
