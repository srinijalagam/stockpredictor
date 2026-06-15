import type { Prediction } from "../types";
import { TradePlanCard } from "./TradePlanCard";

const REC_CLASS: Record<string, string> = {
  STRONG_BUY: "rec-buy",
  BUY: "rec-buy",
  ACCUMULATE: "rec-buy",
  HOLD: "rec-hold",
  WAIT: "rec-hold",
  SELL: "rec-sell",
  AVOID: "rec-sell",
};

export function PredictionPanel({ prediction }: { prediction: Prediction }) {
  const recClass = REC_CLASS[prediction.recommendation] ?? "rec-hold";
  const confidencePct = Math.round((prediction.confidence ?? 0) * 100);
  const price =
    prediction.current_price != null
      ? new Intl.NumberFormat(undefined, {
          style: "currency",
          currency: prediction.currency || "USD",
        }).format(prediction.current_price)
      : "—";

  return (
    <div className="card prediction-card">
      <div className="prediction-header">
        <div>
          <h2>
            {prediction.company_name}{" "}
            <span className="ticker">{prediction.ticker}</span>
          </h2>
          <p className="muted">
            As of {prediction.as_of} · Current price {price}
          </p>
        </div>
        <div className="rec-block">
          <span className={`rec-pill ${recClass}`}>
            {prediction.recommendation.replace("_", " ")}
          </span>
          <div className="confidence">
            <div className="confidence-bar">
              <div className="confidence-fill" style={{ width: `${confidencePct}%` }} />
            </div>
            <span className="muted">{confidencePct}% confidence</span>
          </div>
        </div>
      </div>

      {prediction.summary && <p className="summary">{prediction.summary}</p>}

      <div className="plans">
        <TradePlanCard title="Entry plan" plan={prediction.entry} accent="entry" />
        <TradePlanCard title="Exit plan" plan={prediction.exit} accent="exit" />
      </div>

      {prediction.strong_reasons?.length > 0 && (
        <div className="reasons">
          <h3>Strong reasons</h3>
          <ul>
            {prediction.strong_reasons.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </div>
      )}

      {prediction.risks?.length > 0 && (
        <div className="reasons risks">
          <h3>Risks</h3>
          <ul>
            {prediction.risks.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </div>
      )}

      {prediction.thought_process?.length > 0 && (
        <details className="reasoning-details">
          <summary>Detailed reasoning ({prediction.thought_process.length} steps)</summary>
          <ol>
            {prediction.thought_process.map((t, i) => (
              <li key={i}>{t}</li>
            ))}
          </ol>
        </details>
      )}

      {prediction.disclaimer && <p className="disclaimer">{prediction.disclaimer}</p>}
    </div>
  );
}
