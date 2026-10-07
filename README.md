# PayPal Guardian

An AI agent that removes payment anxiety. Built for the **Build What's Next with PayPal and AI** hackathon.

Three modules, one agent, powered by live PayPal data:

1. **Verification Shield** — paste a claimed payment, AI cross-checks it against real PayPal order data to catch fake screenshots, phishing claims, and scams.
2. **Pre-Payment Trust Score** — before sending money to a new counterparty, AI scores the risk based on available signals and gives a plain-language recommendation.
3. **Subscription Radar** — scans PayPal transaction history to surface recurring charges before they stack up.

## Why this matters

Payment anxiety is real and mostly unsolved: fake payment proof scams, no way to assess a stranger before sending money, forgotten subscriptions quietly draining accounts. PayPal has the data to fix all three. This project puts an AI agent on top of that data to actually do it.

## Tech stack

- **PayPal**: REST API (Orders, Transaction Search, Webhooks) via sandbox
- **AI**: Groq (Llama 3.3 70B) for verification reasoning and risk scoring
- **Backend**: FastAPI (Python)
- **Frontend**: React + TypeScript + Vite

## Setup

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# fill in PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET from developer.paypal.com/dashboard
# fill in GROQ_API_KEY from console.groq.com (free tier)
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open `http://localhost:5173`.

## PayPal integration details

- **Orders API** (`/v2/checkout/orders/{id}`) — pulls real-time order status for Verification Shield to compare against user claims.
- **Transaction Search API** (`/v1/reporting/transactions`) — powers Subscription Radar by pulling 90-day transaction history and grouping by merchant.
- **Webhooks** (`/api/webhooks/paypal`) — listens for `PAYMENT.CAPTURE.COMPLETED` and related events as a live ground-truth feed, with signature verification against PayPal's notification API.

## AI integration details

Groq (Llama 3.3 70B) powers two reasoning tasks:
- Comparing a user's claimed payment text against actual PayPal order data, returning a verified/flagged verdict with reasoning.
- Scoring counterparty risk from available signals (account age, prior transaction history) before a payment is sent.

## License

MIT
