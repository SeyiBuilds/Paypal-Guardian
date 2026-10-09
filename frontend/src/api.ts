const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export interface VerifyResult {
  order_id: string;
  claimed_text: string;
  actual_status: string;
  result: {
    verified: boolean;
    confidence: "high" | "medium" | "low";
    reasoning: string;
  };
  timestamp: string;
}

export interface TrustResult {
  counterparty_email: string;
  result: {
    risk_level: "low" | "medium" | "high";
    score: number;
    reasoning: string;
    recommendation: string;
  };
  timestamp: string;
}

export interface Subscription {
  merchant: string;
  charge_count: number;
  charges: { value: string; currency_code: string }[];
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export const api = {
  verifyClaim: (claimed_text: string, order_id: string) =>
    post<VerifyResult>("/api/verify-claim", { claimed_text, order_id }),

  getVerificationFeed: () =>
    get<{ events: VerifyResult[] }>("/api/verification-feed"),

  trustScore: (counterparty_email: string, known_signals: Record<string, unknown>) =>
    post<TrustResult>("/api/trust-score", { counterparty_email, known_signals }),

  subscriptionRadar: () =>
    get<{ subscriptions: Subscription[]; window_days: number }>("/api/subscription-radar"),
};
