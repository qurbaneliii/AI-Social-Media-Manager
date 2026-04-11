# FILE: apps/content-analysis/Dockerfile
FROM python:3.12-slim AS builder
WORKDIR /build
COPY apps/content-analysis/requirements.txt .
RUN pip install --upgrade pip && pip install --prefix=/install -r requirements.txt

FROM python:3.12-slim AS runtime
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
RUN useradd -u 1001 -m aria
WORKDIR /app
COPY --from=builder /install /usr/local
COPY packages/types/src/types_shared /app/types_shared
COPY apps/content-analysis /app
ENV PYTHONPATH=/app
USER aria
EXPOSE 8000
HEALTHCHECK CMD curl -f http://localhost:8000/health || exit 1
ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
