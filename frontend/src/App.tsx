import VerificationShield from "./components/VerificationShield";
import TrustScore from "./components/TrustScore";
import SubscriptionRadar from "./components/SubscriptionRadar";
import "./App.css";

export default function App() {
  return (
    <div className="app">
      <header>
        <h1>PayPal Guardian</h1>
        <p>An AI agent that removes payment anxiety — verify, assess, and track, powered by live PayPal data.</p>
      </header>

      <main className="grid">
        <VerificationShield />
        <TrustScore />
        <SubscriptionRadar />
      </main>
    </div>
  );
}
