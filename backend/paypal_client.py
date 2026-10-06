"""
PayPal Sandbox API client.
Handles OAuth2 token fetch + wraps REST calls used by PayPal Guardian.
"""
import os
import time
import httpx

PAYPAL_BASE_URL = os.getenv("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")
CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET", "")

_token_cache = {"access_token": None, "expires_at": 0}


async def get_access_token() -> str:
    """Fetch (and cache) an OAuth2 access token from PayPal sandbox."""
    now = time.time()
    if _token_cache["access_token"] and _token_cache["expires_at"] > now + 30:
        return _token_cache["access_token"]

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{PAYPAL_BASE_URL}/v1/oauth2/token",
            auth=(CLIENT_ID, CLIENT_SECRET),
            data={"grant_type": "client_credentials"},
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()
        _token_cache["access_token"] = data["access_token"]
        _token_cache["expires_at"] = now + data.get("expires_in", 3200)
        return _token_cache["access_token"]


async def paypal_request(method: str, path: str, json_body: dict | None = None) -> dict:
    """Generic authenticated request to PayPal REST API."""
    token = await get_access_token()
    async with httpx.AsyncClient() as client:
        resp = await client.request(
            method,
            f"{PAYPAL_BASE_URL}{path}",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=json_body,
        )
        resp.raise_for_status()
        return resp.json() if resp.content else {}


async def get_transaction_history(start_date: str, end_date: str) -> dict:
    """
    Pull transaction history for Subscription Radar + Trust Score context.
    PayPal Transaction Search API. Dates in ISO 8601.
    """
    path = (
        f"/v1/reporting/transactions"
        f"?start_date={start_date}&end_date={end_date}&fields=all"
    )
    return await paypal_request("GET", path)


async def get_order(order_id: str) -> dict:
    """Fetch a specific order/payment to verify its real status."""
    return await paypal_request("GET", f"/v2/checkout/orders/{order_id}")


async def verify_webhook_signature(headers: dict, body: dict, webhook_id: str) -> dict:
    """Verify an incoming webhook actually came from PayPal (anti-spoof)."""
    payload = {
        "auth_algo": headers.get("paypal-auth-algo"),
        "cert_url": headers.get("paypal-cert-url"),
        "transmission_id": headers.get("paypal-transmission-id"),
        "transmission_sig": headers.get("paypal-transmission-sig"),
        "transmission_time": headers.get("paypal-transmission-time"),
        "webhook_id": webhook_id,
        "webhook_event": body,
    }
    return await paypal_request("POST", "/v1/notifications/verify-webhook-signature", payload)
