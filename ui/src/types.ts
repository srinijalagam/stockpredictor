export interface Source {
  title: string;
  url: string;
  publisher: string;
  snippet: string;
  kind: "yahoo" | "web" | "company" | "filing";
}

export interface PriceRange {
  low: number | null;
  high: number | null;
  currency: string;
}

export interface TradePlan {
  price_range: PriceRange;
  time_window: string;
  start_date: string | null;
  end_date: string | null;
  rationale: string;
}

export interface Prediction {
  ticker: string;
  company_name: string;
  as_of: string;
  current_price: number | null;
  currency: string;
  recommendation: string;
  confidence: number;
  entry: TradePlan;
  exit: TradePlan;
  strong_reasons: string[];
  risks: string[];
  thought_process: string[];
  summary: string;
  disclaimer: string;
}

export interface PredictResponse {
  prediction: Prediction;
  sources: Source[];
  steps: string[];
  warnings: string[];
}

export interface StepEvent {
  node: string;
  label: string;
  details: string[];
}
