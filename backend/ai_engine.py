"""
AI reasoning layer — Groq (Llama 3.3 70B) powers Verification Shield and Trust Score.
"""
import os
import json
from groq import Groq

MODEL = "llama-3.3-70b-versatile"
_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY not set — add it to backend/.env")
        _client = Groq(api_key=api_key)
    return _client


def verify_payment_claim(claimed_text: str, actual_transaction: dict) -> dict:
    """
    Compare what a user claims about a payment vs real PayPal transaction data.
    Returns verified/flagged + reasoning. Used by Verification Shield.
    """
    prompt = f"""You are a payment fraud detector. Compare the user's claim about a payment
against the ACTUAL transaction data pulled live from PayPal's API.

USER'S CLAIM:
{claimed_text}

ACTUAL PAYPAL TRANSACTION DATA:
{json.dumps(actual_transaction, indent=2)}

Decide if the claim matches reality. Look for mismatches in amount, status, sender,
date, or any sign of a fabricated/doctored claim (e.g. claiming "completed" when
status is "pending" or "denied").

Respond ONLY with valid JSON in this exact shape:
{{"verified": true or false, "confidence": "high" or "medium" or "low", "reasoning": "one or two sentences, plain language"}}"""

    completion = _get_client().chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    return json.loads(completion.choices[0].message.content)


def score_trust(counterparty_signals: dict) -> dict:
    """
    Score risk of sending money to a new counterparty based on available signals.
    Used by Pre-Payment Trust Score module.
    """
    prompt = f"""You are a payment risk analyst. Assess the risk of sending money to this
PayPal counterparty based on the signals below. Be conservative — when signals are
thin or missing, that itself raises risk (new/unverified accounts are higher risk).

COUNTERPARTY SIGNALS:
{json.dumps(counterparty_signals, indent=2)}

Respond ONLY with valid JSON in this exact shape:
{{"risk_level": "low" or "medium" or "high", "score": 0-100 (0=safest), "reasoning": "one or two sentences, plain language", "recommendation": "one short actionable sentence"}}"""

    completion = _get_client().chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    return json.loads(completion.choices[0].message.content)
