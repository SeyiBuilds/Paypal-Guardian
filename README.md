# PayPal Guardian

An AI agent that removes payment anxiety. Built for the **Build What's Next with PayPal and AI** hackathon.

Guardian runs on live PayPal sandbox data and answers three questions people worry about whenever money moves.

| Module | Question | PayPal API | AI role |
| --- | --- | --- | --- |
| **Verification Shield** | "Did they really pay me?" | Orders v2, Webhooks | Compares a pasted claim to the real order, returns Verified or Flagged with reasoning |
| **Pre-Payment Trust Score** | "Is it safe to pay this person?" | None directly (uses user-supplied signals) | Scores risk 0 to 100 with a recommendation |
| **Subscription Radar** | "What keeps charging me?" | Transaction Search | None (groups repeat charges) |

The backend fetches the real order from PayPal first, and the model only reasons over that retrieved data.

**Stack:** FastAPI + httpx (Python 3.10+), React + TypeScript + Vite, Groq (`openai/gpt-oss-120b` by default), PayPal REST sandbox.

## Quick start

**Prerequisites:** Python 3.10+, Node 18+, Git, a free [PayPal Developer](https://developer.paypal.com) account with a Sandbox app (Apps & Credentials > Sandbox > Create App), and a free [Groq](https://console.groq.com) API key.

### 1. Backend

```bash
git clone https://github.com/SeyiBuilds/Paypal-Guardian.git
cd Paypal-Guardian/backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # Windows: copy .env.example .env
```

Fill in `backend/.env` with no quotes or spaces:

| Variable | Paste | Required |
| --- | --- | --- |
| `PAYPAL_CLIENT_ID` | Client ID of your Sandbox app | Yes |
| `PAYPAL_CLIENT_SECRET` | Secret of the same app | Yes |
| `GROQ_API_KEY` | Your Groq key | Yes |
| `GROQ_MODEL` | A chat model your key can use (`python list_models.py` lists them) | No |
| `PAYPAL_WEBHOOK_ID` | Webhook ID (see Webhooks below) | No |

Verify credentials, then start the API:

```bash
python check_credentials.py     # expect: SUCCESS: PayPal accepted these credentials.
uvicorn main:app --reload --port 8000
```

`http://localhost:8000/health` should return `{"status":"ok"}`. API docs are at `/docs`.

### 2. Demo data

In a second terminal (venv active, inside `backend/`):

```bash
python seed_sandbox.py create
```

It creates four sandbox orders and prints an approve link for each.

| # | Description | Amount | Do this |
| --- | --- | --- | --- |
| 1 | Logo design, unpaid | 150.00 | Nothing (stays `CREATED`) |
| 2 | Website landing page, approved not captured | 400.00 | Approve only |
| 3 | Monthly website retainer | 75.00 | Approve, then capture |
| 4 | Monthly website retainer | 75.00 | Approve, then capture |

Open the links for orders 2, 3, 4 and approve with your sandbox **Personal** account (Sandbox > Accounts). Then:

```bash
python seed_sandbox.py capture ORDER_ID_3
python seed_sandbox.py capture ORDER_ID_4
python seed_sandbox.py status   # 1 CREATED, 2 APPROVED, 3 and 4 COMPLETED
```

### 3. Frontend

```bash
cd ../frontend
npm install
cp .env.example .env            # Windows: copy .env.example .env
npm run dev
```

Open the URL Vite prints (default `http://localhost:5173`). If the backend is not on port 8000, set `VITE_API_BASE` in `frontend/.env` and restart Vite.

## Trying it

Use the order IDs from the seed script.

**Verification Shield**

| Order | Paste this claim | Expected |
| --- | --- | --- |
| 1 | `I paid the $150 logo invoice` | Flagged, order is still `CREATED` |
| 3 | `I paid $75 for the monthly retainer` | Verified, order is `COMPLETED` |
| 2 | `I paid $400 for the landing page` | Flagged, `APPROVED` but never captured |

**Pre-Payment Trust Score**

| Email | Account age | Prior txns | Expected |
| --- | --- | --- | --- |
| `newseller123@gmail.com` | `2 days` | `0` | High risk |
| `client@example.com` | `3 years` | `12` | Low or medium risk |

**Subscription Radar** loads on its own and lists repeat charges from the last 90 days. The two $75 retainer captures should show as one recurring charge. Sandbox history can lag by a few hours, and **Transaction Search** must be enabled on your app (Features section, tick it, save).

## Webhooks (optional)

1. Expose the backend, for example `ngrok http 8000`.
2. In your Sandbox app add a webhook at `https://YOUR-NGROK-URL/api/webhooks/paypal` for `Payment capture completed` and `Checkout order approved`.
3. Copy the Webhook ID into `PAYPAL_WEBHOOK_ID` and restart the backend.
4. Send a test from the Webhook Simulator. The backend replies `{"status":"received"}`.

With a Webhook ID set, events are checked via PayPal's `verify-webhook-signature`. In sandbox, verification issues are tolerated so simulator traffic does not break the demo.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/verify-claim` | `order_id`, `claimed_text` in, AI verdict out |
| GET | `/api/verification-feed` | Recent verifications |
| POST | `/api/trust-score` | `counterparty_email`, `known_signals` in, risk out |
| GET | `/api/subscription-radar` | Repeat charges, last 90 days |
| POST | `/api/webhooks/paypal` | Webhook receiver |
| GET | `/health` | Liveness |

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `401 invalid_client` | Wrong Client ID or Secret, or stray spaces or quotes. Run `python check_credentials.py` |
| `model_not_found` (Groq) | Run `python list_models.py`, set `GROQ_MODEL` |
| `Failed to fetch` in the UI | Backend not running on the port in `VITE_API_BASE`, or it errored. Check its terminal |
| `{"detail":"Not Found"}` in the UI | Another app owns that port. Use a free port and update `VITE_API_BASE` |
| Radar is empty | Transaction Search not enabled, or sandbox history has not caught up |
| `pydantic-core` build fails | Upgrade pip, or use a Python version with prebuilt wheels |

## Limitations

In-memory storage (resets on restart). Trust scores rely on user-supplied signals because sandbox accounts expose limited history. Radar infers recurrence from repeat payers and amounts, not billing agreements. CORS is open for local development and should be restricted before deploying.

## License

MIT. See [LICENSE](LICENSE).
