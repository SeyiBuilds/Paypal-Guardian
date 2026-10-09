import { useEffect, useState } from "react";
import { api, type Subscription } from "../api";

export default function SubscriptionRadar() {
  const [subs, setSubs] = useState<Subscription[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .subscriptionRadar()
      .then((res) => setSubs(res.subscriptions))
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="panel">
      <h2>Subscription Radar</h2>
      <p className="subtitle">Recurring charges detected in your PayPal history (90 days)</p>

      {loading && <div className="muted">Scanning...</div>}
      {error && <div className="error">{error}</div>}
      {!loading && !error && subs.length === 0 && (
        <div className="muted">No recurring charges found yet.</div>
      )}

      {subs.map((s) => (
        <div key={s.merchant} className="sub-row">
          <span className="merchant">{s.merchant}</span>
          <span className="count">{s.charge_count}x charges</span>
        </div>
      ))}
    </div>
  );
}
