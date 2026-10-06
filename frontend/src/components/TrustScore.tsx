import { useState } from "react";
import { api, type TrustResult } from "../api";

export default function TrustScore() {
  const [email, setEmail] = useState("");
  const [accountAge, setAccountAge] = useState("");
  const [priorTxns, setPriorTxns] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<TrustResult | null>(null);
  const [error, setError] = useState("");

  async function handleCheck() {
    setLoading(true);
    setError("");
    try {
      const res = await api.trustScore(email, {
        claimed_account_age: accountAge || "unknown",
        prior_transaction_count: priorTxns || "unknown",
      });
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Trust check failed");
    } finally {
      setLoading(false);
    }
  }

  const riskColor = { low: "#16a34a", medium: "#d97706", high: "#dc2626" };

  return (
    <div className="panel">
      <h2>🔍 Pre-Payment Trust Score</h2>
      <p className="subtitle">Check risk before sending money to a new counterparty</p>

      <input
        placeholder="Counterparty PayPal email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />
      <input
        placeholder="Account age (if known, e.g. '2 weeks')"
        value={accountAge}
        onChange={(e) => setAccountAge(e.target.value)}
      />
      <input
        placeholder="Prior transactions with you (if any)"
        value={priorTxns}
        onChange={(e) => setPriorTxns(e.target.value)}
      />
      <button onClick={handleCheck} disabled={loading || !email}>
        {loading ? "Analyzing..." : "Check Trust Score"}
      </button>

      {error && <div className="error">{error}</div>}

      {result && (
        <div className="result-card" style={{ borderColor: riskColor[result.result.risk_level] }}>
          <div className="result-header">
            <span style={{ color: riskColor[result.result.risk_level] }}>
              {result.result.risk_level.toUpperCase()} RISK
            </span>
            <span className="confidence">score: {result.result.score}/100</span>
          </div>
          <p>{result.result.reasoning}</p>
          <div className="recommendation">→ {result.result.recommendation}</div>
        </div>
      )}
    </div>
  );
}
