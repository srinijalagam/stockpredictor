import type { PredictResponse, StepEvent } from "./types";

export interface StreamHandlers {
  onStatus?: (message: string) => void;
  onStep?: (step: StepEvent) => void;
  onResult?: (result: PredictResponse) => void;
  onError?: (message: string) => void;
}

/**
 * Subscribe to the agent's SSE stream. Calls /api (same origin) which nginx
 * proxies to the agent service, so the agent can be swapped independently.
 * Returns a cleanup function that closes the connection.
 */
export function streamPrediction(query: string, handlers: StreamHandlers): () => void {
  const url = `/api/predict/stream?query=${encodeURIComponent(query)}`;
  const es = new EventSource(url);

  es.addEventListener("status", (e) => {
    try {
      handlers.onStatus?.(JSON.parse((e as MessageEvent).data).message);
    } catch {
      /* ignore */
    }
  });

  es.addEventListener("step", (e) => {
    try {
      handlers.onStep?.(JSON.parse((e as MessageEvent).data) as StepEvent);
    } catch {
      /* ignore */
    }
  });

  es.addEventListener("result", (e) => {
    try {
      handlers.onResult?.(JSON.parse((e as MessageEvent).data) as PredictResponse);
    } catch (err) {
      handlers.onError?.(String(err));
    }
    es.close();
  });

  es.addEventListener("error", (e) => {
    const msg = (e as MessageEvent)?.data;
    if (msg) {
      try {
        handlers.onError?.(JSON.parse(msg).message);
      } catch {
        handlers.onError?.("Connection error.");
      }
    } else {
      handlers.onError?.("Connection lost. Is the agent service running?");
    }
    es.close();
  });

  return () => es.close();
}
