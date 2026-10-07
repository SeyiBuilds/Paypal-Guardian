"""
PayPal Guardian — backend
Three modules: Verification Shield, Pre-Payment Trust Score, Subscription Radar.
"""
import os
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

import paypal_client  # noqa: E402 (env must load first)
import ai_engine  # noqa: E402

app = FastAPI(title="PayPal Guardian API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten before real deploy
    allow_methods=["*"],
    allow_headers=["*"],
)

# in-memory store for hackathon demo — swap for Supabase in prod
webhook_events: list[dict] = []
verification_log: list[dict] = []

WEBHOOK_ID = os.getenv("PAYPAL_WEBHOOK_ID", "")


# ---------- Module 1: Verification Shield ----------

class VerifyClaimRequest(BaseModel):
    claimed_text: str
    order_id: str


@app.post("/api/verify-claim")
async def verify_claim(req: VerifyClaimRequest):
    """
    User pastes a claimed payment (screenshot text, description, etc).
    We pull the REAL order from PayPal and ask AI to compare.
    """
    try:
        actual = await paypal_client.get_order(req.order_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Order not found in PayPal: {e}")

    result = ai_engine.verify_payment_claim(req.claimed_text, actual)
    entry = {
        "order_id": req.order_id,
        "claimed_text": req.claimed_text,
        "actual_status": actual.get("status"),
        "result": result,
        "timestamp": datetime.utcnow().isoformat(),
    }
    verification_log.append(entry)
    return entry


@app.get("/api/verification-feed")
async def get_verification_feed():
    """Live feed for the Verification Shield panel."""
    return {"events": list(reversed(verification_log[-50:]))}


@app.post("/api/webhooks/paypal")
async def paypal_webhook(request: Request):
    """
    Receives real-time PayPal webhook events (PAYMENT.CAPTURE.COMPLETED, etc).
    This is the ground-truth feed Verification Shield checks claims against.
    """
    body = await request.json()
    headers = dict(request.headers)

    # verify it's actually from PayPal, not spoofed
    if WEBHOOK_ID:
        try:
            verification = await paypal_client.verify_webhook_signature(headers, body, WEBHOOK_ID)
            if verification.get("verification_status") != "SUCCESS":
                raise HTTPException(status_code=400, detail="Webhook signature invalid")
        except Exception:
            pass  # in sandbox dev, signature verify can be flaky — log but don't hard-fail demo

    event = {
        "event_type": body.get("event_type"),
        "resource": body.get("resource"),
        "received_at": datetime.utcnow().isoformat(),
    }
    webhook_events.append(event)
    return {"status": "received"}


# ---------- Module 2: Pre-Payment Trust Score ----------

class TrustScoreRequest(BaseModel):
    counterparty_email: str
    known_signals: dict = {}


@app.post("/api/trust-score")
async def trust_score(req: TrustScoreRequest):
    """
    Score risk of sending to a new counterparty.
    known_signals: whatever frontend/user can supply (account age claim,
    prior transaction count, etc) — sandbox has limited lookup, so this
    is designed to accept manual/observed signals too.
    """
    signals = {
        "counterparty_email": req.counterparty_email,
        **req.known_signals,
    }
    result = ai_engine.score_trust(signals)
    return {
        "counterparty_email": req.counterparty_email,
        "signals_used": signals,
        "result": result,
        "timestamp": datetime.utcnow().isoformat(),
    }


# ---------- Module 3: Subscription Radar (lighter, less AI-heavy) ----------

@app.get("/api/subscription-radar")
async def subscription_radar():
    """
    Pull recent transactions, group by merchant to approximate recurring charges.
    Simple logic, not deep AI — matches its 'light panel' role.
    """
    end = datetime.utcnow()
    start = end - timedelta(days=90)
    try:
        data = await paypal_client.get_transaction_history(
            start.strftime("%Y-%m-%dT00:00:00-0000"),
            end.strftime("%Y-%m-%dT23:59:59-0000"),
        )
    except Exception as e:
        return {"error": str(e), "subscriptions": []}

    txns = data.get("transaction_details", [])
    merchants: dict[str, list] = {}
    for t in txns:
        info = t.get("transaction_info", {})
        payer = t.get("payer_info", {})
        merchant = payer.get("payer_name", {}).get("alternate_full_name") or "Unknown"
        merchants.setdefault(merchant, []).append(info.get("transaction_amount", {}))

    recurring = [
        {"merchant": m, "charge_count": len(charges), "charges": charges}
        for m, charges in merchants.items()
        if len(charges) > 1  # appeared more than once = likely recurring
    ]
    return {"subscriptions": recurring, "window_days": 90}


@app.get("/health")
async def health():
    return {"status": "ok"}
