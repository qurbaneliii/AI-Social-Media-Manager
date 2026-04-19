# AI-Social-Media-Manager

## Canonical runtime

Use repository-root runtime only:

- Compose file: `/docker-compose.yml`
- Environment file: `/.env` (copied from `/.env.example`)
- Backend bind target: `0.0.0.0:8000`

Do not treat `aria/docker-compose.yml` as the default entrypoint.

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

Open:

- Frontend: http://localhost:3000
- Backend health: http://localhost:8000/health

## Supported local toolchain

- Python 3.12.x
- Node.js 20.x
- Docker Compose v2

Python 3.14 is currently unsupported for this repository runtime.

## Setup and troubleshooting

- [Local Run Guide](LOCAL_RUN_GUIDE.md)
- [Full System Architecture](docs/full-system-architecture.md)
