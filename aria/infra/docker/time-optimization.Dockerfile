# FILE: infra/docker/time-optimization.Dockerfile
FROM python:3.12-slim AS base
WORKDIR /app
COPY apps/time-optimization /app
RUN pip install --no-cache-dir fastapi uvicorn pydantic
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
