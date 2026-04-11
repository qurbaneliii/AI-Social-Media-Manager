# ARIA Monorepo

Implementation workspace for ARIA (Automated Reach & Intelligence Architect).

## Local Setup

1. Copy env template and adjust provider/OAuth credentials as needed.

```bash
cp .env.example .env
```

2. Install Python dependencies.

```bash
pip install -r requirements.txt
```

3. Start infrastructure and services.

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
