import { useEffect, useState } from "react";
import VerificationShield from "./components/VerificationShield";
import TrustScore from "./components/TrustScore";
import SubscriptionRadar from "./components/SubscriptionRadar";
import { api } from "./api";
import "./App.css";

export default function App() {
  const [online, setOnline] = useState<boolean | null>(null);

  useEffect(() => {
    api.health().then(() => setOnline(true)).catch(() => setOnline(false));
  }, []);

  return (
    <div className="app">
      <header className="top">
        <div className="brand">
          <svg width="30" height="34" viewBox="0 0 30 34" aria-hidden="true">
            <path d="M15 1 2 6v10c0 8 5.5 14 13 17 7.5-3 13-9 13-17V6L15 1Z" fill="none" stroke="#2f9bff" strokeWidth="2" />
            <path d="m9 17 4 4 8-9" fill="none" stroke="#2f9bff" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <div>
            <h1>PayPal Guardian</h1>
            <p>An AI agent that takes the anxiety out of payments.</p>
          </div>
        </div>
        <div className={`status ${online === false ? "status-off" : ""}`}>
          <span className="dot" />
          {online === null ? "Connecting" : online ? "Sandbox live" : "Backend offline"}
        </div>
      </header>

      <main className="grid">
        <VerificationShield />
        <TrustScore />
        <SubscriptionRadar />
      </main>

      <footer>Powered by the PayPal REST API and Groq. Sandbox data only.</footer>
    </div>
  );
}
