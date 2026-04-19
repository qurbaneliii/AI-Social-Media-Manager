# ARIA Monorepo

Implementation workspace for ARIA (Automated Reach & Intelligence Architect).

## Runtime status

`aria/docker-compose.yml` is no longer the canonical default for full-project startup.
Use repository-root `docker-compose.yml` and root `.env` for reproducible local/Codespaces/Docker behavior.

## Local Setup

1. Create the canonical root environment file.

```bash
cp ../.env.example ../.env
```

2. Install Python dependencies (Python 3.12).

```bash
pip install -r requirements.txt
```

3. (Optional, ARIA-only) start ARIA-only stack with root env.

```bash
docker compose up -d postgres redis temporal minio
docker compose up -d api worker temporal-worker
```

4. Apply database migrations.

```bash
python -m db.migrate
```

5. Register the Temporal namespace used by workflows.

```bash
docker compose exec temporal tctl --ns aria namespace register --rd 3
```

6. Create the MinIO bucket for media uploads.

```bash
docker compose exec minio sh -c 'mkdir -p /data/${MINIO_BUCKET:-aria-media}'
```

7. Install spaCy English model for onboarding brand analysis.

```bash
python -m spacy download en_core_web_sm
```

## Section 8 API Surface

- `POST /v1/onboarding/company-profile`
- `POST /v1/onboarding/vocabulary`
- `POST /v1/onboarding/import`
- `POST /v1/onboarding/quality-check`
- `GET /v1/onboarding/status/{company_id}`
- `POST /v1/posts/generate`
- `GET /v1/posts/{post_id}`
- `POST /v1/schedules`
- `GET /v1/schedules/{schedule_id}`
- `POST /v1/webhooks/{platform}`
- `POST /v1/media/presign`
- `POST /v1/media/confirm/{asset_id}`
- `GET /v1/oauth/connect`
- `GET /v1/oauth/callback`
