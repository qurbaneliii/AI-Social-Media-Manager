# LOCAL RUN GUIDE

## 1) Requirements

- Docker Desktop (latest stable)
- Docker Compose v2

## 2) Environment Setup

From repository root:

PowerShell:
Copy-Item .env.example .env

bash/zsh:
cp .env.example .env

Minimum values to review in .env:
- JWT_SECRET
- OPENAI_API_KEY (optional; if empty, AI endpoints use local deterministic fallback)

## 3) One-Command Startup

From repository root:

docker compose up --build

This starts:
- aria-frontend on http://localhost:3000
- aria-api on http://localhost:8000
- postgres on 5432
- redis on 6379
- temporal on 7233
- minio on 9000/9001
- aria-worker
- aria-db-migrate (runs once, then exits successfully)

## 4) Verify Services

Health checks:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/health

## 5) MVP User Flow (Register -> Login -> AI)

1. Open http://localhost:3000/register
2. Create a user account
3. Login at http://localhost:3000/login
4. Open the AI content page at http://localhost:3000/posts/new
5. Use AI Studio actions (Generate, Improve, Analyze, Suggest hashtags/topics)

Notes:
- AI Studio works even without OPENAI_API_KEY via deterministic local fallback responses.
- For real model outputs, set OPENAI_API_KEY in .env and restart containers.

## 6) Stop Everything

From repository root:

docker compose down

To also remove volumes (fresh DB next run):

docker compose down -v
