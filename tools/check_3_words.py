#!/usr/bin/env python3
"""Проверка 3 слов для теста"""

import os, sys
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))

from db import get_db_connection
from check_words_ai import check_word_with_ai, mark_word_as_checked
import time

conn = get_db_connection()
cur = conn.cursor()

# Берём 3 непроверенных или старых слова
cur.execute("""
    SELECT id, de, ru, article, verb_forms 
    FROM words 
    ORDER BY ai_checked_at ASC NULLS FIRST 
    LIMIT 3
""")

words = cur.fetchall()
print(f"Check {len(words)} words...\n")

start = time.time()
for row in words:
    word_id, de, ru, article, verb_forms = row
    print(f"Check: {de}...", end=" ")
    
    result, error = check_word_with_ai(de, ru, article, verb_forms)
    
    if error:
        print(f"Error: {error[:50]}")
    elif result.get('valid'):
        print("OK")
    else:
        print(f"Errors: {result.get('errors', [])}")
    
    mark_word_as_checked(conn, word_id)

elapsed = time.time() - start
print(f"\nTime: {elapsed:.1f} sec ({elapsed/len(words):.1f} sec/word)")

cur.close()
conn.close()
print("\n✅ Готово!")
