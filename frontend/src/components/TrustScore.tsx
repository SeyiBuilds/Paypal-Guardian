import { useState } from "react";
import { api, type TrustResult } from "../api";

const PRESETS = [
  { label: "Brand new account", email: "newseller123@gmail.com", age: "2 days", txns: "0" },
  { label: "Repeat client", email: "returning.client@example.com", age: "3 years", txns: "12" },
];

const RISK_COLOR = { low: "var(--ok)", medium: "var(--warn)", high: "var(--bad)" };

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
    setResult(null);
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

  const risk = result?.result.risk_level;

  return (
    <section className="panel">
      <div className="panel-tag">02 / Assess</div>
      <h2>Pre-Payment Trust Score</h2>
      <p className="subtitle">Check the risk before you send money to someone new.</p>

      <div className="chips">
        {PRESETS.map((p) => (
          <button
            key={p.label}
            type="button"
            className="chip"
            onClick={() => {
              setEmail(p.email);
              setAccountAge(p.age);
              setPriorTxns(p.txns);
              setResult(null);
            }}
          >
            {p.label}
          </button>
        ))}
      </div>

      <input
        placeholder="Counterparty PayPal email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />
      <div className="row">
        <input
          placeholder="Account age, e.g. 2 weeks"
          value={accountAge}
          onChange={(e) => setAccountAge(e.target.value)}
        />
        <input
          placeholder="Prior txns with you"
          value={priorTxns}
          onChange={(e) => setPriorTxns(e.target.value)}
        />
      </div>
      <button onClick={handleCheck} disabled={loading || !email}>
        {loading ? "Analyzing..." : "Check Trust Score"}
      </button>

      {error && <div className="error">{error}</div>}

      {result && risk && (
        <div className="result-card" style={{ borderColor: RISK_COLOR[risk] }}>
          <div className="result-header">
            <span className="risk-label" style={{ color: RISK_COLOR[risk] }}>
              {risk.toUpperCase()} RISK
            </span>
            <span className="confidence">{result.result.score}/100</span>
          </div>
          <div className="meter">
            <div
              className="meter-fill"
              style={{ width: `${result.result.score}%`, background: RISK_COLOR[risk] }}
            />
          </div>
          <p>{result.result.reasoning}</p>
          <div className="recommendation">Recommendation: {result.result.recommendation}</div>
        </div>
      )}
    </section>
  );
}
