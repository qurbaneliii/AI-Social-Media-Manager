# FILE: infra/docker/llm-orchestration.Dockerfile
FROM python:3.12-slim AS base
WORKDIR /app
COPY apps/llm-orchestration /app
RUN pip install --no-cache-dir fastapi uvicorn pydantic
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
