# syntax=docker/dockerfile:1

# ---- Build stage ----
FROM node:20-alpine AS build
WORKDIR /app

COPY package.json ./
# Use install (no lockfile committed) to fetch deps, then build static assets.
RUN npm install

COPY tsconfig.json vite.config.ts index.html ./
COPY src ./src
RUN npm run build

# ---- Serve stage ----
FROM nginx:1.27-alpine AS serve

# nginx will envsubst this template at startup using AGENT_HOST / AGENT_PORT.
ENV AGENT_HOST=agent \
    AGENT_PORT=8000
COPY default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://127.0.0.1:80/ >/dev/null 2>&1 || exit 1
