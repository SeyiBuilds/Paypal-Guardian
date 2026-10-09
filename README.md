# PayPal Guardian

An AI agent that removes payment anxiety. Built for the **Build What's Next with PayPal and AI** hackathon.

Guardian sits on top of live PayPal sandbox data and answers three questions people worry about every time money moves:

| Module | The question it answers | PayPal API used | AI role |
| --- | --- | --- | --- |
| **Verification Shield** | "Did this person really pay me?" | Orders v2, Webhooks | Compares a pasted payment claim against the real order and returns Verified or Flagged with reasoning |
| **Pre-Payment Trust Score** | "Is it safe to send money to this person?" | OAuth, account signals | Scores counterparty risk from 0 to 100 and gives a plain-language recommendation |
| **Subscription Radar** | "What is quietly charging me?" | Transaction Search | None (deterministic grouping of repeat charges) |

## Why this matters

Fake payment screenshots, unvetted strangers, and forgotten recurring charges are all problems of trust in payment data. PayPal holds the ground truth for all three. Guardian puts an AI layer on that data so a person gets a clear answer instead of guessing.

## How it works

```
React + Vite UI  -->  FastAPI backend  -->  PayPal REST API (sandbox)
                            |
                            +-->  Groq LLM (verdicts and risk scoring)
                            ^
        PayPal webhooks ----+   (live payment events)
```

The AI never decides alone. For Verification Shield the backend first fetches the real order from PayPal, then asks the model to compare the claim against that data. The model only reasons over facts the backend retrieved.

## Tech stack

- **PayPal**: REST API sandbox (Orders v2, Transaction Search, Webhooks with signature verification)
- **AI**: Groq, default model `openai/gpt-oss-120b` (configurable)
- **Backend**: FastAPI, httpx, pydantic (Python 3.10+)
- **Frontend**: React, TypeScript, Vite

## Quick start

### Prerequisites

- Python 3.10 or newer, Node.js 18 or newer, Git
- A free PayPal Developer account with a **Sandbox** REST app (developer.paypal.com > Apps & Credentials > Sandbox > Create App)
- A free Groq API key (console.groq.com)
- A sandbox **Personal** and **Business** account (created by default under Sandbox > Accounts)

### 1. Clone

```bash
git clone https://github.com/SeyiBuilds/Paypal-Guardian.git
cd Paypal-Guardian
```

### 2. Backend

macOS and Linux:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Windows (cmd):

```bat
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Open `backend/.env` and fill in the values:

| Variable | What to paste | Required |
| --- | --- | --- |
| `PAYPAL_CLIENT_ID` | Client ID from your Sandbox app | Yes |
| `PAYPAL_CLIENT_SECRET` | Secret from the same app | Yes |
| `PAYPAL_BASE_URL` | Leave as `https://api-m.sandbox.paypal.com` | Yes |
| `GROQ_API_KEY` | Your Groq key | Yes |
| `GROQ_MODEL` | A chat model your key can use. Run `python list_models.py` to see options | No (defaults to `openai/gpt-oss-120b`) |
| `PAYPAL_WEBHOOK_ID` | ID of a webhook on your app (see Webhooks below) | No |

Paste values with no quotes and no spaces. To confirm your PayPal credentials are accepted before going further:

```bash
python check_credentials.py
```

You should see `SUCCESS: PayPal accepted these credentials.`

Start the API:

```bash
uvicorn main:app --reload --port 8000
```

Check `http://localhost:8000/health` returns `{"status":"ok"}`. Interactive API docs are at `http://localhost:8000/docs`.

### 3. Create demo data

In a second terminal, with the backend venv active:

```bash
cd backend
python seed_sandbox.py create
```

This creates four sandbox orders in different states and prints an approve link for each:

| # | Description | Amount | Target state |
| --- | --- | --- | --- |
| 1 | Logo design, unpaid | 150.00 | Leave as `CREATED` |
| 2 | Website landing page, approved not captured | 400.00 | Approve only |
| 3 | Monthly website retainer, paid | 75.00 | Approve, then capture |
| 4 | Monthly website retainer, paid | 75.00 | Approve, then capture |

Open the approve links for orders 2, 3 and 4 and log in with your sandbox **Personal** account to approve. Then capture 3 and 4:

```bash
python seed_sandbox.py capture ORDER_ID_3
python seed_sandbox.py capture ORDER_ID_4
python seed_sandbox.py status
```

`status` should show order 1 as `CREATED`, order 2 as `APPROVED`, and orders 3 and 4 as `COMPLETED`.

### 4. Frontend

```bash
cd frontend
npm install
cp .env.example .env        # Windows: copy .env.example .env
npm run dev
```

Open the URL Vite prints (default `http://localhost:5173`). If you started the backend on a port other than 8000, set `VITE_API_BASE` in `frontend/.env` to match and restart Vite.

## Trying it

Use the order IDs printed by the seed script. These inputs show each outcome:

**Verification Shield**

| Order ID | Claim to paste | Expected result |
| --- | --- | --- |
| Order 1 | `I paid the $150 logo invoice` | Flagged. The order is still `CREATED`, so no payment happened |
| Order 3 | `I paid $75 for the monthly retainer` | Verified. The order is `COMPLETED` for $75 |
| Order 2 | `I paid $400 for the landing page` | Flagged. The order is `APPROVED` but was never captured |

**Pre-Payment Trust Score**

| Email | Account age | Prior transactions | Expected result |
| --- | --- | --- | --- |
| `newseller123@gmail.com` | `2 days` | `0` | High risk |
| `client@example.com` | `3 years` | `12` | Low risk |

**Subscription Radar** loads automatically. It lists payers who made repeated charges of the same amount in the last 90 days. With the seed data, the two $75 retainer captures appear as one recurring charge. PayPal sandbox history can take up to a few hours to show new transactions, and the app needs the **Transaction Search** feature enabled (see below).

## Optional setup

### Enable Transaction Search

Subscription Radar reads PayPal's Transaction Search API. In the developer dashboard open your app, scroll to **Features**, tick **Transaction Search**, and save.

### Webhooks (live payment events)

Webhooks let PayPal push events such as `PAYMENT.CAPTURE.COMPLETED` to the backend.

1. Expose the backend publicly, for example `ngrok http 8000`.
2. In your Sandbox app, add a webhook with the URL `https://YOUR-NGROK-URL/api/webhooks/paypal`.
3. Subscribe to `Payment capture completed` and `Checkout order approved`.
4. Copy the Webhook ID into `PAYPAL_WEBHOOK_ID` in `backend/.env` and restart the backend.
5. Send a test event from the Webhook Simulator in the dashboard. The backend replies `{"status":"received"}`.

If `PAYPAL_WEBHOOK_ID` is set, incoming events are checked against PayPal's `verify-webhook-signature` endpoint. In sandbox the app logs verification problems instead of rejecting events so simulator traffic does not break the demo.

## API reference

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/verify-claim` | Body: `order_id`, `claimed_text`. Fetches the real order and returns the AI verdict |
| GET | `/api/verification-feed` | Recent verification results |
| POST | `/api/trust-score` | Body: `counterparty_email`, `known_signals`. Returns risk level, score, recommendation |
| GET | `/api/subscription-radar` | Repeat charges found in the last 90 days |
| POST | `/api/webhooks/paypal` | PayPal webhook receiver |
| GET | `/health` | Liveness check |

## Troubleshooting

| Symptom | Likely cause and fix |
| --- | --- |
| `401 invalid_client` from PayPal | Wrong or mismatched Client ID and Secret, or stray spaces or quotes in `.env`. Run `python check_credentials.py` |
| `model_not_found` from Groq | The default model is not enabled for your key. Run `python list_models.py` and set `GROQ_MODEL` |
| `Failed to fetch` in the browser | Backend is not running on the port in `VITE_API_BASE`, or it returned an error. Check the backend terminal |
| `{"detail":"Not Found"}` in the UI | Another app is using the port. Start the backend on a free port and update `VITE_API_BASE` |
| Subscription Radar shows nothing | Transaction Search not enabled on the app, or sandbox history has not caught up yet |
| `pip install` fails building `pydantic-core` | Use a Python version with prebuilt wheels, or upgrade pip first |

## Limitations

- Data is in memory. The verification feed and webhook log reset when the backend restarts.
- Trust scores rely on the signals the user supplies, because sandbox accounts expose limited public history.
- Subscription Radar infers recurring charges by grouping repeat payers and amounts. It does not read PayPal billing agreements.
- CORS is open for local development and should be restricted before any real deployment.

## License

MIT. See [LICENSE](LICENSE).
