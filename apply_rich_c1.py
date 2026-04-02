
import os, sys, json
import psycopg2
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env.local'))

client = OpenAI(api_key=os.environ.get("GROQ_API_KEY"), base_url="https://api.groq.com/openai/v1")
conn = psycopg2.connect(os.environ.get("POSTGRES_URL"))
cur = conn.cursor()

PROMPT_TEMPLATE = """Ты - эксперт по немецкому языку. Обогати слово данными.
Слово: {de}
Перевод: {ru}
Верни ТОЛЬКО JSON:
{{
  "ru": "перевод1, перевод2",
  "topic": "Тема",
  "article": "der|die|das|",
  "verb_forms": "forms",
  "plural": "plural",
  "examples": [{{"de": "...", "ru": "..."}}],
  "synonyms": "син1, син2",
  "antonyms": "ант1, ант2",
  "collocations": "колл1, колл2, колл3"
}}
"""

# Берем 10 слов C1
cur.execute("SELECT id, de, ru FROM words WHERE level = 'C1' AND ai_checked_at IS NULL LIMIT 10")
words = cur.fetchall()

for w_id, de, ru in words:
    print(f"Enriching: {de}...")
    prompt = PROMPT_TEMPLATE.format(de=de, ru=ru)
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        response_format={"type": "json_object"}
    )
    data = json.loads(resp.choices[0].message.content)
    
    cur.execute("""
        UPDATE words 
        SET ru = %s, topic = %s, article = %s, verb_forms = %s, plural = %s, 
            synonyms = %s, antonyms = %s, collocations = %s, examples = %s,
            ai_checked_at = NOW()
        WHERE id = %s
    """, (
        data.get('ru'), data.get('topic'), data.get('article'), data.get('verb_forms'), data.get('plural'),
        data.get('synonyms'), data.get('antonyms'), data.get('collocations'), 
        json.dumps(data.get('examples')), w_id
    ))
    conn.commit()

cur.close()
conn.close()
print("✅ Done! 10 C1 words updated.")
