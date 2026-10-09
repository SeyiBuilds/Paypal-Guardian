import { useEffect, useState } from "react";
import { api, type DemoOrder, type VerifyResult } from "../api";

export default function VerificationShield() {
  const [orderId, setOrderId] = useState("");
  const [claimText, setClaimText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<VerifyResult | null>(null);
  const [error, setError] = useState("");
  const [demo, setDemo] = useState<DemoOrder[]>([]);
  const [feed, setFeed] = useState<VerifyResult[]>([]);

  async function refreshFeed() {
    try {
      const res = await api.getVerificationFeed();
      setFeed(res.events.slice(0, 5));
    } catch {
      /* feed is optional */
    }
  }

  useEffect(() => {
    api.demoOrders().then((r) => setDemo(r.orders)).catch(() => {});
    refreshFeed();
  }, []);

  async function handleVerify() {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await api.verifyClaim(claimText, orderId.trim());
      setResult(res);
      refreshFeed();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Verification failed");
    } finally {
      setLoading(false);
    }
  }

  function fill(o: DemoOrder) {
    setOrderId(o.id);
    setClaimText(`I paid $${o.amount} for ${o.description.split(",")[0].toLowerCase()}`);
    setResult(null);
    setError("");
  }

  return (
    <section className="panel">
      <div className="panel-tag">01 / Verify</div>
      <h2>Verification Shield</h2>
      <p className="subtitle">Paste a claimed payment. We check it against the real PayPal order.</p>

      {demo.length > 0 && (
        <div className="chips">
          {demo.map((o, i) => (
            <button key={o.id} type="button" className="chip" onClick={() => fill(o)}>
              {i + 1}. ${o.amount}
            </button>
          ))}
        </div>
      )}

      <input
        placeholder="PayPal Order ID"
        value={orderId}
        onChange={(e) => setOrderId(e.target.value)}
      />
      <textarea
        placeholder="What was claimed, e.g. 'I paid you $150 for the logo'"
        rows={3}
        value={claimText}
        onChange={(e) => setClaimText(e.target.value)}
      />
      <button onClick={handleVerify} disabled={loading || !orderId || !claimText}>
        {loading ? "Checking..." : "Verify Claim"}
      </button>

      {error && <div className="error">{error}</div>}

      {result && (
        <div className={`result-card ${result.result.verified ? "verified" : "flagged"}`}>
          <div className="result-header">
            <span className={`pill ${result.result.verified ? "pill-ok" : "pill-bad"}`}>
              {result.result.verified ? "Verified" : "Flagged"}
            </span>
            <span className="confidence">confidence: {result.result.confidence}</span>
          </div>
          <p>{result.result.reasoning}</p>
          <div className="meta">PayPal status: {result.actual_status}</div>
        </div>
      )}

      {feed.length > 0 && (
        <div className="feed">
          <div className="feed-title">Recent checks</div>
          {feed.map((f, i) => (
            <div key={i} className="feed-row">
              <span className={`dot ${f.result.verified ? "dot-ok" : "dot-bad"}`} />
              <span className="feed-id">{f.order_id}</span>
              <span className="feed-status">{f.actual_status}</span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
