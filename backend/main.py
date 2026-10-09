"""
PayPal Guardian — backend
Three modules: Verification Shield, Pre-Payment Trust Score, Subscription Radar.
"""
import os
import re
import asyncio
import httpx
from datetime import datetime, timedelta, timezone
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
ORDER_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
MAX_STORED = 500


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
    if not ORDER_ID_RE.match(req.order_id):
        raise HTTPException(status_code=422, detail="Invalid order_id")
    try:
        actual = await paypal_client.get_order(req.order_id)
    except httpx.HTTPStatusError as e:
        code = 404 if e.response.status_code == 404 else 502
        raise HTTPException(status_code=code, detail=f"PayPal error: {e}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"PayPal error: {e}")

    try:
        result = await asyncio.to_thread(ai_engine.verify_payment_claim, req.claimed_text, actual)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI error: {e}")
    entry = {
        "order_id": req.order_id,
        "claimed_text": req.claimed_text,
        "actual_status": actual.get("status"),
        "result": result,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    verification_log.append(entry)
    del verification_log[:-MAX_STORED]
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
        except Exception:
            raise HTTPException(status_code=502, detail="Webhook verification unavailable")
        if verification.get("verification_status") != "SUCCESS":
            raise HTTPException(status_code=400, detail="Webhook signature invalid")

    event = {
        "event_type": body.get("event_type"),
        "resource": body.get("resource"),
        "received_at": datetime.now(timezone.utc).isoformat(),
    }
    webhook_events.append(event)
    del webhook_events[:-MAX_STORED]
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
    try:
        result = await asyncio.to_thread(ai_engine.score_trust, signals)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI error: {e}")
    return {
        "counterparty_email": req.counterparty_email,
        "signals_used": signals,
        "result": result,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ---------- Module 3: Subscription Radar (lighter, less AI-heavy) ----------

@app.get("/api/subscription-radar")
async def subscription_radar():
    """
    Pull recent transactions, group by merchant to approximate recurring charges.
    Simple logic, not deep AI — matches its 'light panel' role.
    """
    # PayPal Transaction Search allows at most 31 days per request, so chunk 90 days
    end = datetime.now(timezone.utc)
    txns: list[dict] = []
    try:
        for i in range(3):
            w_end = end - timedelta(days=30 * i)
            w_start = w_end - timedelta(days=30)
            data = await paypal_client.get_transaction_history(
                w_start.strftime("%Y-%m-%dT%H:%M:%S-0000"),
                w_end.strftime("%Y-%m-%dT%H:%M:%S-0000"),
            )
            txns.extend(data.get("transaction_details", []))
    except Exception as e:
        detail = str(e)
        resp = getattr(e, "response", None)
        if resp is not None:
            detail = f"{resp.status_code}: {resp.text[:300]}"
        return {"error": f"Transaction Search failed ({detail})", "subscriptions": []}

    # group by (payer, amount): same person paying the same amount repeatedly
    groups: dict[tuple, dict] = {}
    for t in txns:
        info = t.get("transaction_info") or {}
        payer = t.get("payer_info") or {}
        amount = info.get("transaction_amount") or {}
        name = (
            (payer.get("payer_name") or {}).get("alternate_full_name")
            or payer.get("email_address")
            or "Unknown"
        )
        key = (name, amount.get("value"), amount.get("currency_code"))
        g = groups.setdefault(
            key,
            {
                "merchant": name,
                "amount": amount.get("value"),
                "currency": amount.get("currency_code"),
                "charge_count": 0,
                "last_charged": None,
            },
        )
        g["charge_count"] += 1
        date = info.get("transaction_initiation_date")
        if date and (g["last_charged"] is None or str(date) > str(g["last_charged"])):
            g["last_charged"] = date

    recurring = sorted(
        (g for g in groups.values() if g["charge_count"] > 1),
        key=lambda g: -g["charge_count"],
    )
    return {
        "subscriptions": recurring,
        "window_days": 90,
        "transactions_scanned": len(txns),
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
