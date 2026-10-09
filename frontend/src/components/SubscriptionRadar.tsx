import { useEffect, useState } from "react";
import { api, type RadarResponse } from "../api";

function fmtDate(d: string | null) {
  if (!d) return "";
  const date = new Date(d);
  return isNaN(date.getTime()) ? "" : date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export default function SubscriptionRadar() {
  const [data, setData] = useState<RadarResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  function load() {
    setLoading(true);
    setError("");
    api
      .subscriptionRadar()
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load"))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  const subs = data?.subscriptions ?? [];

  return (
    <section className="panel">
      <div className="panel-tag">03 / Track</div>
      <h2>Subscription Radar</h2>
      <p className="subtitle">Repeat charges found in your last 90 days of PayPal history.</p>

      {loading && <div className="muted">Scanning...</div>}
      {error && <div className="error">{error}</div>}
      {data?.error && <div className="error">{data.error}</div>}

      {!loading && !error && !data?.error && subs.length === 0 && (
        <div className="empty">
          <div>No repeat charges yet.</div>
          <div className="muted">
            Scanned {data?.transactions_scanned ?? 0} transactions. Sandbox history can take a few hours to appear.
          </div>
        </div>
      )}

      {subs.map((s) => (
        <div key={`${s.merchant}-${s.amount}`} className="sub-row">
          <div>
            <div className="merchant">{s.merchant}</div>
            <div className="muted">
              {s.charge_count} charges{s.last_charged ? `, last on ${fmtDate(s.last_charged)}` : ""}
            </div>
          </div>
          <div className="amount">
            {s.amount} {s.currency}
          </div>
        </div>
      ))}

      <button type="button" className="ghost" onClick={load} disabled={loading}>
        Rescan
      </button>
    </section>
  );
}
