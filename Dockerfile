# syntax=docker/dockerfile:1

FROM node:22-alpine AS web-builder
WORKDIR /app/web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
ARG VITE_API_BASE_URL=
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

COPY python/requirements-runtime.txt ./python/requirements-runtime.txt
RUN pip install --no-cache-dir -r python/requirements-runtime.txt

COPY VERSION CHANGELOG.md ./
COPY python/web_api.py ./python/web_api.py
COPY python/src ./python/src
COPY python/data/processed ./python/data/processed
COPY python/data/instances ./python/data/instances
COPY --from=web-builder /app/web/dist ./web/dist

RUN useradd --create-home --shell /bin/sh appuser \
    && chown -R appuser:appuser /app

USER appuser
EXPOSE 8000

CMD ["sh", "-c", "uvicorn web_api:app --app-dir python --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips=*"]
