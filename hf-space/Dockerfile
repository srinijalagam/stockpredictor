# syntax=docker/dockerfile:1
# Single-container build for Hugging Face Spaces (sdk: docker).
# Build context = the assembled Space root (see deploy script), which contains
# agent/, ui/ and serve.py.

# ---- Stage 1: build the React UI ----
FROM node:20-alpine AS ui
WORKDIR /ui
COPY ui/package.json ./
RUN npm install
COPY ui/tsconfig.json ui/vite.config.ts ui/index.html ./
COPY ui/src ./src
RUN npm run build

# ---- Stage 2: Python runtime serving UI + API on one port ----
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # HF Spaces runs containers as a non-root user; keep caches in a writable dir.
    HOME=/tmp \
    PORT=7860

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY agent/requirements.txt ./
RUN pip install -r requirements.txt

COPY agent/app ./app
COPY serve.py ./serve.py
COPY --from=ui /ui/dist ./static

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=5s --start-period=25s --retries=3 \
    CMD curl -fsS http://localhost:${PORT:-7860}/health || exit 1

# Shell form so ${PORT} is expanded (HF sets PORT; defaults to 7860).
CMD uvicorn serve:app --host 0.0.0.0 --port ${PORT:-7860}
