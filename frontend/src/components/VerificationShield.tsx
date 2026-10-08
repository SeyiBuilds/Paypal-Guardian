import { useState } from "react";
import { api, type VerifyResult } from "../api";

export default function VerificationShield() {
  const [orderId, setOrderId] = useState("");
  const [claimText, setClaimText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<VerifyResult | null>(null);
  const [error, setError] = useState("");

  async function handleVerify() {
    setLoading(true);
    setError("");
    try {
      const res = await api.verifyClaim(claimText, orderId);
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Verification failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="panel">
      <h2>Verification Shield</h2>
      <p className="subtitle">Paste a claimed payment, we check it against real PayPal data</p>

      <input
        placeholder="PayPal Order ID"
        value={orderId}
        onChange={(e) => setOrderId(e.target.value)}
      />
      <textarea
        placeholder="Paste the claim (e.g. screenshot text, 'payment of $500 completed')"
        value={claimText}
        onChange={(e) => setClaimText(e.target.value)}
        rows={3}
      />
      <button onClick={handleVerify} disabled={loading || !orderId || !claimText}>
        {loading ? "Checking..." : "Verify Claim"}
      </button>

      {error && <div className="error">{error}</div>}

      {result && (
        <div className={`result-card ${result.result.verified ? "verified" : "flagged"}`}>
          <div className="result-header">
            {result.result.verified ? "Verified" : "Flagged"}
            <span className="confidence">confidence: {result.result.confidence}</span>
          </div>
          <p>{result.result.reasoning}</p>
          <div className="meta">actual status: {result.actual_status}</div>
        </div>
      )}
    </div>
  );
}
