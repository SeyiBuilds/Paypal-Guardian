"""
Seed PayPal sandbox with demo orders in different states.

Usage (from backend/, venv active):
    python seed_sandbox.py create            create 4 demo orders, print approve links
    python seed_sandbox.py status            show live status of the saved orders
    python seed_sandbox.py capture ORDER_ID  capture an APPROVED order (becomes COMPLETED)

Demo plan:
    1. create
    2. open the approve links for orders 2, 3 and 4 and approve with your sandbox personal account
    3. capture orders 3 and 4
    Result: order 1 = CREATED, order 2 = APPROVED, orders 3 and 4 = COMPLETED
"""
import asyncio
import json
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

HERE = Path(__file__).parent
load_dotenv(HERE / ".env")

import paypal_client  # noqa: E402 (env must load first)

STORE = HERE / "seed_orders.json"

DEMO_ORDERS = [
    ("Logo design, unpaid", "150.00"),
    ("Website landing page, approved not captured", "400.00"),
    ("Monthly website retainer, paid", "75.00"),
    ("Monthly website retainer, paid", "75.00"),
]


def load_store() -> list[dict]:
    return json.loads(STORE.read_text()) if STORE.exists() else []


def save_store(items: list[dict]) -> None:
    STORE.write_text(json.dumps(items, indent=2))


def approve_link(order: dict) -> str:
    for link in order.get("links", []):
        if link.get("rel") in ("approve", "payer-action"):
            return link["href"]
    return ""


async def create_orders() -> None:
    saved = []
    for i, (desc, value) in enumerate(DEMO_ORDERS, start=1):
        body = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "reference_id": f"guardian-demo-{i}",
                    "description": desc,
                    "amount": {"currency_code": "USD", "value": value},
                }
            ],
        }
        order = await paypal_client.paypal_request("POST", "/v2/checkout/orders", body)
        saved.append({"id": order["id"], "description": desc, "amount": value})
        print(f"[{i}] {order['id']}  {value} USD  status={order['status']}")
        print(f"    {desc}")
        print(f"    approve: {approve_link(order)}\n")
    save_store(saved)
    print(f"Saved to {STORE.name}")


async def show_status() -> None:
    items = load_store()
    if not items:
        print("No saved orders. Run: python seed_sandbox.py create")
        return
    for i, item in enumerate(items, start=1):
        order = await paypal_client.get_order(item["id"])
        print(f"[{i}] {item['id']}  {item['amount']} USD  status={order['status']}  ({item['description']})")


async def capture(order_id: str) -> None:
    result = await paypal_client.paypal_request(
        "POST", f"/v2/checkout/orders/{order_id}/capture", {}
    )
    print(f"{order_id} -> {result.get('status')}")


async def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "create":
        await create_orders()
    elif cmd == "status":
        await show_status()
    elif cmd == "capture" and len(sys.argv) > 2:
        await capture(sys.argv[2])
    else:
        print(__doc__)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except httpx.HTTPStatusError as e:
        print(f"PayPal error {e.response.status_code}: {e.response.text}")
        sys.exit(1)
