"""FastAPI application exposing the stock prediction agent."""
from __future__ import annotations

import asyncio
import json
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from . import __version__
from .config import get_settings
from .graph.builder import get_graph
from .models import PredictRequest, PredictResponse, Prediction, Source

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stockpredictor")

settings = get_settings()
app = FastAPI(title="Stock Predictor Agent", version=__version__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

_NODE_LABELS = {
    "resolve": "Resolving ticker / company",
    "market": "Studying Yahoo Finance data",
    "news": "Searching trusted analyst & news sources",
    "filings": "Reading company website & filings",
    "predict": "Synthesizing grounded prediction",
}


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "version": __version__,
        "llm_configured": settings.has_llm,
        "search": "tavily" if settings.tavily_api_key else "duckduckgo",
    }


def _accumulate(acc: dict, update: dict) -> None:
    """Merge a LangGraph node update into the accumulator state."""
    for value in update.values():
        if not isinstance(value, dict):
            continue
        for key, val in value.items():
            if key in {"sources", "steps", "warnings"}:
                acc.setdefault(key, [])
                acc[key].extend(val or [])
            else:
                acc[key] = val


def _build_response(acc: dict, query: str) -> PredictResponse:
    prediction: Prediction = acc.get("prediction") or Prediction(
        ticker=acc.get("ticker", ""),
        company_name=acc.get("company_name", ""),
        summary="No prediction was produced.",
    )
    # De-duplicate sources by URL.
    seen: set[str] = set()
    sources: list[Source] = []
    for s in acc.get("sources", []):
        key = s.url or s.title
        if key and key not in seen:
            seen.add(key)
            sources.append(s)
    return PredictResponse(
        prediction=prediction,
        sources=sources,
        steps=acc.get("steps", []),
        warnings=acc.get("warnings", []),
    )


@app.post("/api/predict", response_model=PredictResponse)
async def predict(req: PredictRequest) -> PredictResponse:
    graph = get_graph()
    acc: dict = {}
    async for update in graph.astream({"query": req.query}, stream_mode="updates"):
        _accumulate(acc, update)
    return _build_response(acc, req.query)


@app.get("/api/predict/stream")
async def predict_stream(query: str):
    """Server-Sent Events stream of agent progress + final result."""
    graph = get_graph()

    async def event_generator():
        acc: dict = {}
        try:
            yield {"event": "status", "data": json.dumps({"message": "Starting analysis…"})}
            async for update in graph.astream({"query": query}, stream_mode="updates"):
                for node_name, value in update.items():
                    _accumulate(acc, {node_name: value})
                    label = _NODE_LABELS.get(node_name, node_name)
                    steps = (value or {}).get("steps", []) if isinstance(value, dict) else []
                    yield {
                        "event": "step",
                        "data": json.dumps({"node": node_name, "label": label, "details": steps}),
                    }
                await asyncio.sleep(0)  # cooperative flush
            response = _build_response(acc, query)
            yield {"event": "result", "data": response.model_dump_json()}
        except Exception as exc:  # noqa: BLE001
            logger.exception("stream failed")
            yield {"event": "error", "data": json.dumps({"message": str(exc)})}

    return EventSourceResponse(event_generator())
