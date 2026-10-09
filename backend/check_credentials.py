"""
Check PayPal sandbox credentials from backend/.env.
Usage (from backend/, venv active):  python check_credentials.py
Prints lengths and problems only, never the secret itself.
"""
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

client_id = os.getenv("PAYPAL_CLIENT_ID", "")
secret = os.getenv("PAYPAL_CLIENT_SECRET", "")
base = os.getenv("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")

problems = []
for name, value in (("PAYPAL_CLIENT_ID", client_id), ("PAYPAL_CLIENT_SECRET", secret)):
    if not value:
        problems.append(f"{name} is empty")
    elif value != value.strip():
        problems.append(f"{name} has leading or trailing spaces")
    elif value[0] in "\"'" or value[-1] in "\"'":
        problems.append(f"{name} has quotes around it, remove them")
    elif value.startswith("your_"):
        problems.append(f"{name} is still the placeholder text")

print(f"Client ID : {len(client_id)} chars, starts with {client_id[:4]!r}")
print(f"Secret    : {len(secret)} chars")
print(f"Base URL  : {base}")

for p in problems:
    print(f"PROBLEM: {p}")
if problems:
    sys.exit(1)

try:
    r = httpx.post(
        f"{base}/v1/oauth2/token",
        auth=(client_id.strip(), secret.strip()),
        data={"grant_type": "client_credentials"},
        timeout=20,
    )
except httpx.HTTPError as e:
    print(f"NETWORK ERROR: {e}")
    sys.exit(1)

if r.status_code == 200:
    print("SUCCESS: PayPal accepted these credentials.")
else:
    print(f"FAILED {r.status_code}: {r.text}")
    print("PayPal rejected the pair. Re-copy both from the Sandbox app page (copy icons).")
    sys.exit(1)
