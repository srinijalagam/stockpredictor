import type { Source } from "../types";

const KIND_LABEL: Record<string, string> = {
  yahoo: "Yahoo Finance",
  web: "Trusted web",
  company: "Company",
  filing: "Filing",
};

export function SourceList({ sources }: { sources: Source[] }) {
  if (!sources.length) return null;
  return (
    <div className="card">
      <h2>Sources ({sources.length})</h2>
      <p className="muted">Grounded on trusted financial sources only.</p>
      <ul className="source-list">
        {sources.map((s, i) => (
          <li key={i} className="source-item">
            <span className={`badge badge-${s.kind}`}>{KIND_LABEL[s.kind] ?? s.kind}</span>
            <div className="source-body">
              {s.url ? (
                <a href={s.url} target="_blank" rel="noreferrer">
                  {s.title || s.url}
                </a>
              ) : (
                <span>{s.title}</span>
              )}
              {s.publisher && <span className="source-pub"> · {s.publisher}</span>}
              {s.snippet && <p className="source-snippet">{s.snippet}</p>}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
