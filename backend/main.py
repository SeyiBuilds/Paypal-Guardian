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

def _parse_date(value):
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            d = datetime.strptime(str(value), fmt)
            return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _frequency(dates):
    """Label a charge series by its typical gap. Returns (label, next_expected_iso)."""
    if len(dates) < 2:
        return "Repeat", None
    gaps = sorted((b - a).total_seconds() / 86400 for a, b in zip(dates, dates[1:]))
    median = gaps[len(gaps) // 2]
    for label, lo, hi, step in (
        ("Weekly", 6, 8, 7),
        ("Monthly", 25, 35, 30),
        ("Yearly", 350, 380, 365),
    ):
        if lo <= median <= hi:
            return label, (dates[-1] + timedelta(days=step)).date().isoformat()
    return "Repeat", None



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

    # Group by (counterparty, amount, currency). Outgoing charges (negative amounts)
    # are labelled by the merchant; incoming ones by the payer.
    groups: dict[tuple, dict] = {}
    for t in txns:
        info = t.get("transaction_info") or {}
        payer = t.get("payer_info") or {}
        ship = t.get("shipping_info") or {}
        amount = info.get("transaction_amount") or {}
        raw = str(amount.get("value") or "")
        outgoing = raw.startswith("-")
        payer_name = (
            (payer.get("payer_name") or {}).get("alternate_full_name")
            or payer.get("email_address")
        )
        if outgoing:
            name = ship.get("name") or info.get("transaction_subject") or payer_name or "Unknown"
        else:
            name = payer_name or "Unknown"
        value = raw.lstrip("-")
        key = (name, value, amount.get("currency_code"), outgoing)
        g = groups.setdefault(
            key,
            {
                "merchant": name,
                "amount": value,
                "currency": amount.get("currency_code"),
                "direction": "outgoing" if outgoing else "incoming",
                "charge_count": 0,
                "last_charged": None,
                "_dates": [],
            },
        )
        g["charge_count"] += 1
        date = info.get("transaction_initiation_date")
        dt = _parse_date(date)
        if dt:
            g["_dates"].append(dt)
        if date and (g["last_charged"] is None or str(date) > str(g["last_charged"])):
            g["last_charged"] = date

    recurring = []
    for g in groups.values():
        if g["charge_count"] < 2:
            continue
        dates = sorted(g.pop("_dates"))
        freq, nxt = _frequency(dates)
        g["frequency"] = freq
        g["next_expected"] = nxt
        recurring.append(g)
    order = {"Monthly": 0, "Weekly": 1, "Yearly": 2, "Repeat": 3}
    recurring.sort(key=lambda g: (order.get(g["frequency"], 3), -g["charge_count"]))
    return {
        "subscriptions": recurring,
        "window_days": 90,
        "transactions_scanned": len(txns),
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
