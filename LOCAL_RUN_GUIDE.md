# LOCAL RUN GUIDE

## 1) Required Software

- Git
- Docker Desktop + Docker Compose v2
- Node.js 20+
- npm 10+
- Python 3.12+

## 2) Repository Setup

From your machine:

```bash
git clone https://github.com/qurbaneliii/AI-Social-Media-Manager.git
cd AI-Social-Media-Manager
```

Create env file from template:

PowerShell:

```powershell
Copy-Item .env.example .env
```

bash/zsh:

```bash
cp .env.example .env
```

## 3) Environment Variables

Main variables used by the integrated local runtime:

- POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_DB: database bootstrap credentials used by docker-compose
- DATABASE_URL: backend PostgreSQL connection
- FRONTEND_DATABASE_URL: frontend auth/prisma PostgreSQL connection
- REDIS_URL: redis connection for backend
- CELERY_BROKER_URL: celery broker
- CELERY_RESULT_BACKEND: celery result backend
- TEMPORAL_HOST: temporal endpoint
- TEMPORAL_NAMESPACE: temporal namespace (default for local)
- TEMPORAL_TASK_QUEUE: temporal task queue
- MINIO_ENDPOINT: object storage endpoint
- MINIO_ACCESS_KEY: object storage access key
- MINIO_SECRET_KEY: object storage secret key
- MINIO_BUCKET: object storage bucket name
- NEXT_PUBLIC_API_BASE_URL: frontend runtime API base
- NEXT_PUBLIC_API_URL: frontend fallback API base
- JWT_SECRET: frontend auth token signing key
- CORS_ORIGINS: allowed browser origins for backend API
- OPENAI_API_KEY: required for frontend AI Studio endpoints under /api/ai/*
- DEEPSEEK_API_KEY / OPENAI_API_KEY / ANTHROPIC_API_KEY / MISTRAL_API_KEY: at least one is required for backend post generation
- OPENAI_MODEL, OPENAI_REQUEST_TIMEOUT_MS, OPENAI_MAX_RETRIES: frontend and backend OpenAI tuning
- LLM_PROVIDER_TIMEOUT_SECONDS, LLM_PROVIDER_MAX_RETRIES: backend provider transport controls
- OPENAI_EMBEDDING_MODEL, OPENAI_EMBEDDING_TIMEOUT_SECONDS, OPENAI_EMBEDDING_MAX_RETRIES: semantic cache controls

AI is configured for real-provider-only execution. No deterministic local AI fallback path is used.

## 4) Recommended Run (One Command)

From repository root:

```bash
docker-compose up --build
```

Run this command from repository root only. Do not run the separate stack inside `aria/docker-compose.yml` unless you intentionally want the ARIA-internal monorepo stack.

Services started:

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Postgres: 5432
- Redis: 6379
- Temporal: 7233
- MinIO API: 9000
- MinIO Console: 9001

## 5) Manual Run (Without Docker for App Processes)

Use this if you want to run backend/frontend directly while infra remains in Docker.

### 5.1 Start infra only

```bash
docker-compose up -d postgres redis temporal minio
```

### 5.2 Run backend manually

```bash
cd aria
python -m venv .venv
```

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

bash/zsh:

```bash
source .venv/bin/activate
```

Load root environment variables into the current shell before starting backend services:

PowerShell:

```powershell
Get-Content ../.env | ForEach-Object {
	if ($_ -match '^[A-Za-z_][A-Za-z0-9_]*=') {
		$name, $value = $_ -split '=', 2
		[System.Environment]::SetEnvironmentVariable($name, $value)
	}
}
```

bash/zsh:

```bash
set -a
source ../.env
set +a
```

Install backend dependencies and migrate DB:

```bash
pip install --upgrade pip
pip install -r requirements.txt
python -m db.migrate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 5.3 Run frontend manually

Open a second terminal:

```bash
cd aria-frontend
npm install
npx prisma generate
npx prisma migrate deploy
npm run dev -- --hostname 0.0.0.0 --port 3000
```

If frontend API calls fail in manual mode, export the same env variables from `../.env` in this second terminal as well.

## 6) MVP Verification Flow

1. Open http://localhost:3000/register
2. Register a user
3. Login at http://localhost:3000/login
4. Open http://localhost:3000/posts/new
5. Use AI Studio actions (generate/improve/analyze/hashtags/topics)
6. Refresh browser and verify session remains active

## 7) Troubleshooting

### Backend fails to connect to database

- Confirm postgres container is healthy
- Verify DATABASE_URL in .env points to postgres service

### Frontend auth routes fail

- Verify FRONTEND_DATABASE_URL is valid
- Re-run:

```bash
cd aria-frontend
npx prisma migrate deploy
```

### CORS errors in browser

- Ensure CORS_ORIGINS includes http://localhost:3000
- Restart backend after changing .env

### AI responses fail

- For AI Studio in the frontend, set OPENAI_API_KEY and restart services
- For backend post generation, set at least one provider key (DEEPSEEK_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY, or MISTRAL_API_KEY)
- Verify keys are valid and have quota

### Rebuild from clean state

```bash
docker-compose down -v
docker-compose up --build
```

## 8) Stop Services

```bash
docker-compose down
```

Remove volumes too (fresh DB next run):

```bash
docker-compose down -v
```
