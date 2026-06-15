import type { TradePlan } from "../types";

function formatRange(low: number | null, high: number | null, currency: string): string {
  const fmt = (n: number) =>
    new Intl.NumberFormat(undefined, {
      style: "currency",
      currency: currency || "USD",
      maximumFractionDigits: 2,
    }).format(n);
  if (low != null && high != null) return `${fmt(low)} – ${fmt(high)}`;
  if (low != null) return `≥ ${fmt(low)}`;
  if (high != null) return `≤ ${fmt(high)}`;
  return "—";
}

export function TradePlanCard({
  title,
  plan,
  accent,
}: {
  title: string;
  plan: TradePlan;
  accent: "entry" | "exit";
}) {
  const dates =
    plan.start_date || plan.end_date
      ? [plan.start_date, plan.end_date].filter(Boolean).join(" → ")
      : "";
  return (
    <div className={`plan-card plan-${accent}`}>
      <h3>{title}</h3>
      <div className="plan-metric">
        <span className="plan-label">Price range</span>
        <span className="plan-value">
          {formatRange(plan.price_range?.low, plan.price_range?.high, plan.price_range?.currency)}
        </span>
      </div>
      <div className="plan-metric">
        <span className="plan-label">Time window</span>
        <span className="plan-value">{plan.time_window || "—"}</span>
      </div>
      {dates && (
        <div className="plan-metric">
          <span className="plan-label">Approx. dates</span>
          <span className="plan-value">{dates}</span>
        </div>
      )}
      {plan.rationale && <p className="plan-rationale">{plan.rationale}</p>}
    </div>
  );
}
