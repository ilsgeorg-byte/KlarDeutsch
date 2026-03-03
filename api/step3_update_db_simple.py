#!/usr/bin/env python3
"""Шаг 3: Обновить БД"""

import os, sys, json
if sys.platform == 'win32':
    sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))

import psycopg2

DRY_RUN = False

conn = psycopg2.connect(os.environ.get("POSTGRES_URL"))
cur = conn.cursor()

with open('results.json', 'r', encoding='utf-8') as f:
    results = json.load(f)

print(f"Processing {len(results)}...")

for r in results:
    if 'error' in r: continue
    
    if r.get('valid'):
        if not DRY_RUN:
            cur.execute("UPDATE words SET ai_checked_at = NOW() WHERE id = %s", (r['id'],))
    else:
        vf = r.get('corrected_verb_forms')
        if isinstance(vf, dict):
            vf = f"{vf.get('Infinitiv','')}, {vf.get('Präteritum','')}, {vf.get('Partizip II','')}"
        
        if not DRY_RUN:
            cur.execute("""UPDATE words SET de=%s,ru=%s,article=%s,verb_forms=%s,example_de=%s,example_ru=%s,ai_checked_at=NOW() WHERE id=%s""",
                (r.get('corrected_de'), r.get('corrected_ru'), r.get('corrected_article'), vf, r.get('corrected_example_de'), r.get('corrected_example_ru'), r['id']))

if not DRY_RUN:
    conn.commit()

cur.close()
conn.close()
print("Done!")
