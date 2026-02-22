import os
import requests
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.local')
load_dotenv(dotenv_path)

api_key = os.getenv("GROQ_API_KEY")
url = "https://api.groq.com/openai/v1/models"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers)
models = response.json()

print("✅ Доступные модели на твоём Groq аккаунте:")
for model in sorted(models.get("data", []), key=lambda x: x["id"]):
    print(f"  - {model['id']}")
