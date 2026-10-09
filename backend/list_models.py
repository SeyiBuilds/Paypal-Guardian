"""
List the Groq models your API key can use.
Usage (from backend/, venv active):  python list_models.py
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

load_dotenv(Path(__file__).parent / ".env")

client = Groq(api_key=os.getenv("GROQ_API_KEY", "").strip())
for m in sorted(client.models.list().data, key=lambda m: m.id):
    print(m.id)
