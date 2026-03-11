#!/usr/bin/env python3
"""Быстрый тест AI проверки"""

import os
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))

from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

# Тестовое слово
de = "Entschuldigung"
ru = "Извинение"
article = "die"

prompt = f"""
Проверь слово: {de} = {ru} (артикль: {article})
Верни JSON: {{"valid": true/false, "errors": []}}
"""

print(f"Проверка: {de} = {ru}")
response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.1,
    max_tokens=200
)

print(f"Ответ: {response.choices[0].message.content[:200]}")
print("✅ Тест пройден!")
