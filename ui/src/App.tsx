import { useRef, useState } from "react";
import { streamPrediction } from "./api";
import type { PredictResponse, StepEvent } from "./types";
import { PredictionPanel } from "./components/PredictionPanel";
import { ProgressTimeline } from "./components/ProgressTimeline";
import { SourceList } from "./components/SourceList";

const EXAMPLES = ["AAPL", "Tesla", "NVDA", "Microsoft", "Amazon"];

export default function App() {
  const [query, setQuery] = useState("");
  const [running, setRunning] = useState(false);
  const [steps, setSteps] = useState<StepEvent[]>([]);
  const [result, setResult] = useState<PredictResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const cleanupRef = useRef<(() => void) | null>(null);

  function run(q: string) {
    const trimmed = q.trim();
    if (!trimmed || running) return;
    cleanupRef.current?.();
    setRunning(true);
    setSteps([]);
    setResult(null);
    setError(null);

    cleanupRef.current = streamPrediction(trimmed, {
      onStep: (step) => setSteps((prev) => [...prev, step]),
      onResult: (res) => {
        setResult(res);
        setRunning(false);
      },
      onError: (msg) => {
        setError(msg);
        setRunning(false);
      },
    });
  }

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    run(query);
  }

  return (
    <div className="app">
      <header className="hero">
        <h1>Stock Timing Agent</h1>
        <p>
          Enter a stock symbol or company name. The AI agent studies Yahoo Finance,
          trusted analyst &amp; news sources, and the company's own disclosures to
          predict <strong>when to enter and exit</strong> — with price and time ranges,
          grounded reasons, and sources.
        </p>

        <form className="search" onSubmit={onSubmit}>
          <input
            type="text"
            value={query}
            placeholder="e.g. AAPL or Apple"
            onChange={(e) => setQuery(e.target.value)}
            disabled={running}
            aria-label="Stock symbol or company name"
          />
          <button type="submit" disabled={running || !query.trim()}>
            {running ? "Analyzing…" : "Predict"}
          </button>
        </form>

        <div className="examples">
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              className="chip"
              disabled={running}
              onClick={() => {
                setQuery(ex);
                run(ex);
              }}
            >
              {ex}
            </button>
          ))}
        </div>
      </header>

      <main className="content">
        {error && <div className="card error">⚠ {error}</div>}

        {result?.warnings?.map((w, i) => (
          <div key={i} className="card warning">
            {w}
          </div>
        ))}

        <ProgressTimeline steps={steps} running={running} />

        {result && (
          <>
            <PredictionPanel prediction={result.prediction} />
            <SourceList sources={result.sources} />
          </>
        )}
      </main>

      <footer className="footer">
        <p className="muted">
          Educational AI analysis · not financial advice. Powered by LangGraph.
        </p>
      </footer>
    </div>
  );
}
