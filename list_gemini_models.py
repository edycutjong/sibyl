import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GOOGLE_API_KEY", "")
if not api_key:
    api_key = os.environ.get("GEMINI_API_KEY", "")

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
resp = requests.get(url)
if resp.status_code == 200:
    for model in resp.json().get("models", []):
        name = model.get("name")
        if "generateContent" in model.get("supportedGenerationMethods", []):
            print(name)
else:
    print(resp.text)
