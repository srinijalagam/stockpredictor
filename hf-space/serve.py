"""Hugging Face Spaces entrypoint.

Serves the built React UI and the agent's FastAPI API on a single port, so the
whole app fits in one Docker Space container. The agent app already registers
``/api/*`` and ``/health``; we add static file serving + an SPA fallback on top.
"""
from __future__ import annotations

from pathlib import Path

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Importing the agent app registers /api/predict, /api/predict/stream, /health,
# and the FastAPI docs routes BEFORE the catch-all below, so they keep priority.
from app.main import app

_STATIC = Path(__file__).parent / "static"
_INDEX = _STATIC / "index.html"

# Hashed, immutable build assets — mount for efficient static serving.
_assets = _STATIC / "assets"
if _assets.is_dir():
    app.mount("/assets", StaticFiles(directory=_assets), name="assets")


@app.get("/")
async def _index() -> FileResponse:
    return FileResponse(_INDEX)


# SPA fallback: serve a real file when it exists (favicon, etc.), otherwise the
# single-page index. Registered last so /api/*, /health and /assets/* win.
@app.get("/{full_path:path}")
async def _spa(full_path: str) -> FileResponse:
    candidate = _STATIC / full_path
    if candidate.is_file():
        return FileResponse(candidate)
    return FileResponse(_INDEX)
