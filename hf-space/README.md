---
title: Stock Predictor
emoji: 📈
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
short_description: AI agent that predicts when to buy/sell a stock.
---

# Stock Predictor — AI timing agent

Enter a **stock ticker or company name** and the agent predicts **when to buy and
sell**, with price ranges, time windows, grounded reasons, its live thought
process, and the sources it used.

It grounds every prediction on Yahoo Finance, a trusted-domain web search, and
the company's own investor-relations pages, then synthesizes an entry/exit plan.

> ⚠️ Educational AI analysis — **not financial advice**.

## Configuration (Space secrets)

Set these under **Settings → Variables and secrets**:

| Name              | Type   | Required | Notes                                              |
| ----------------- | ------ | -------- | -------------------------------------------------- |
| `OPENAI_API_KEY`  | secret | yes      | LLM key (e.g. Google Gemini OpenAI-compat key).    |
| `OPENAI_BASE_URL` | secret | no       | e.g. `https://generativelanguage.googleapis.com/v1beta/openai/` for Gemini. |
| `OPENAI_MODEL`    | variable | no     | e.g. `gemini-2.5-flash`. Defaults to `gpt-4o-mini`. |
| `TAVILY_API_KEY`  | secret | no       | Better grounded search; falls back to DuckDuckGo.  |

The build and deploy specifics live in this repo's `hf-space/` folder — see
`hf-space/DEPLOY.md`.
