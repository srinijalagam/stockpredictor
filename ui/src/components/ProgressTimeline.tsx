import type { StepEvent } from "../types";

export function ProgressTimeline({
  steps,
  running,
}: {
  steps: StepEvent[];
  running: boolean;
}) {
  if (!steps.length && !running) return null;
  return (
    <div className="card">
      <h2>Agent thought process</h2>
      <ol className="timeline">
        {steps.map((s, i) => (
          <li key={i} className="timeline-item done">
            <div className="timeline-dot" />
            <div>
              <strong>{s.label}</strong>
              {s.details?.map((d, j) => (
                <p key={j} className="muted">
                  {d}
                </p>
              ))}
            </div>
          </li>
        ))}
        {running && (
          <li className="timeline-item active">
            <div className="timeline-dot spin" />
            <div>
              <strong>Working…</strong>
            </div>
          </li>
        )}
      </ol>
    </div>
  );
}
