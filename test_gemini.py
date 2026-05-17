import os
from litellm import completion
from dotenv import load_dotenv

load_dotenv()
try:
    response = completion(model="gemini/gemini-1.5-flash", messages=[{"role": "user", "content": "hi"}])
    print("gemini/gemini-1.5-flash works")
except Exception as e:
    print("gemini/gemini-1.5-flash failed:", e)

try:
    response = completion(model="gemini/gemini-1.5-flash-latest", messages=[{"role": "user", "content": "hi"}])
    print("gemini/gemini-1.5-flash-latest works")
except Exception as e:
    print("gemini/gemini-1.5-flash-latest failed:", e)

try:
    response = completion(model="gemini/gemini-1.5-pro", messages=[{"role": "user", "content": "hi"}])
    print("gemini/gemini-1.5-pro works")
except Exception as e:
    print("gemini/gemini-1.5-pro failed:", e)
