# Local Run Guide (Canonical Runtime)

## 1) Required software

- Docker Desktop + Docker Compose v2
- Python **3.12.x** (only; do not use 3.14 for this project)
- Node.js **20.x**
- npm 10+

## 2) One canonical environment file

From repository root:

```bash
cp .env.example .env
```

Do not maintain separate `.env` files for root, `aria`, and `aria-frontend`.
The canonical runtime uses **root `.env` only**.

## 3) Canonical Docker run

From repository root:

```bash
docker compose up --build
```

Expected ports:

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Postgres: 5432
- Redis: 6379
- Temporal: 7233
- MinIO API: 9000
- MinIO Console: 9001
- Redpanda/Kafka: 9092

## 4) Canonical local venv run (without Docker for app processes)

### 4.1 Start infra only

```bash
docker compose up -d postgres redis temporal minio redpanda
```

### 4.2 Backend in local venv

```bash
cd aria
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -c "import sys; assert sys.version_info[:2] == (3, 12), f'Python 3.12 required, found {sys.version_info.major}.{sys.version_info.minor}'"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
set -a && source ../.env && set +a
python -m db.migrate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4.3 Frontend in second terminal

```bash
cd aria-frontend
npm install
set -a && source ../.env && set +a
npx prisma generate
npx prisma migrate deploy
npm run dev -- --hostname 0.0.0.0 --port 3000
```

## 5) Codespaces run

Codespaces should use the devcontainer configuration at `.devcontainer/devcontainer.json`.
After Codespace starts:

```bash
cp .env.example .env
docker compose up --build
```

## 6) Environment diagnostics checklist

Run from repository root:

```bash
python3.12 --version
which python3.12
docker compose config >/tmp/compose.rendered.yml
test -f .env && echo ".env present"
docker compose ps
curl -fsS http://localhost:8000/health
curl -I http://localhost:3000
```

## 7) Failure signatures and recovery

### Backend not listening on `:8000`

- Verify `api` container is running: `docker compose ps`
- Inspect logs: `docker compose logs api --tail=200`
- Confirm command includes `--host 0.0.0.0 --port 8000`

### Frontend cannot reach backend

- Ensure `NEXT_PUBLIC_API_BASE_URL` in `.env` is `http://localhost:8000`
- Restart frontend container/process after `.env` changes

### Python/NumPy/C-extension mismatch

- Use Python 3.12 only
- Recreate venv and reinstall dependencies:

```bash
cd aria
rm -rf .venv
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Git path confusion / “not a git repository”

- Always run commands from the repository root directory.

## 8) Cleanup stale Python/Jupyter residue

```bash
jupyter kernelspec list
```

Remove stale kernels that reference deleted venvs:

```bash
jupyter kernelspec remove <kernel-name>
```

Then recreate a clean kernel from active venv:

```bash
cd aria
source .venv/bin/activate
python -m pip install ipykernel
python -m ipykernel install --user --name aria-venv --display-name "Python (aria-venv)"
```
