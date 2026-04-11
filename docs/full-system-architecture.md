# Section 1 - Full System Architecture

## 1.1 Component Map

| # | Component | Type | Primary Responsibility | Recommended Technology Stack | Hosting Tier |
|---|---|---|---|---|---|
| 1 | ARIA Dashboard | Web App | Onboarding, post generation, approvals, analytics UX | TypeScript, Next.js 15, React 19, TanStack Query, Zod, Tailwind | Vercel Pro or AWS Amplify + CloudFront |
| 2 | API Gateway | Edge Gateway | TLS termination, auth enforcement, rate limits, WAF, request routing | Kong Gateway or AWS API Gateway + AWS WAF | Managed edge |
| 3 | Identity Provider | Auth Service | User auth, SSO, MFA, token issuance, org membership | Auth0 (preferred) or Keycloak (self-hosted) | Managed SaaS or Kubernetes |
| 4 | ARIA Core API | Backend Monolith (modular) | Tenant CRUD, orchestration entrypoints, policy checks, response assembly | TypeScript, NestJS, Fastify, Prisma | Kubernetes (EKS/GKE/AKS) |
| 5 | LLM Orchestration Service | Microservice | Prompt assembly, model routing, retries, structured output validation, cost controls | Python 3.12, FastAPI, Pydantic v2, Tenacity, LiteLLM-style adapter | Kubernetes autoscaling |
| 6 | Content Analysis Service | Microservice | NLP analysis of historical posts, tone extraction, topic modeling, brand voice fingerprint generation | Python, spaCy, scikit-learn, BERTopic, sentence-transformers | Kubernetes autoscaling |
| 7 | Visual Understanding Service | Microservice | Image analysis: palette, typography inference, layout, visual style, OCR | Python, OpenCV, Pillow, CLIP, Tesseract/Textract | Kubernetes, optional GPU pool |
| 8 | Hashtag and SEO Service | Microservice | Hashtag candidate generation and ranking, SEO metadata generation | Python FastAPI, pgvector search, deterministic ranking rules | Kubernetes autoscaling |
| 9 | Audience Targeting Service | Microservice | Structured audience inference and platform segment mapping | Python FastAPI, feature pipeline + LLM reasoning | Kubernetes autoscaling |
| 10 | Time Optimization Service | Microservice | Best posting windows by platform, confidence scoring, cold-start strategy | Python, LightGBM, statsmodels/Prophet, rules engine | Kubernetes autoscaling |
| 11 | Scheduler and Automation Service | Workflow + Workers | Schedule lifecycle, approvals, publish retries, dead-letter, callbacks | Temporal (preferred) or BullMQ + Redis, Go or Node.js workers | Kubernetes dedicated worker nodes |
| 12 | Platform Integration Layer | Adapter Services | Canonical-to-platform payload mapping, publishing, analytics pulling, webhook normalization | Node.js TypeScript, platform SDKs + REST clients | Kubernetes autoscaling |
| 13 | Event Bus | Stream/Queue | Async event propagation between services, decoupling and replay | Kafka (Confluent/AWS MSK), optional RabbitMQ for simple jobs | Managed cluster |
| 14 | Operational Database | Relational DB | Source of truth for tenants, posts, schedules, credentials metadata, prompt versions | PostgreSQL 15 | AWS Aurora PostgreSQL / RDS |
| 15 | Vector Store | Vector Database | Embeddings for brand voice memory, hashtag and audience retrieval | PostgreSQL pgvector (primary), Qdrant optional at large scale | Same VPC managed DB |
| 16 | Object Storage | Blob Store | Media uploads, brand assets, guidelines PDF, derivatives | Amazon S3 | Managed object storage |
| 17 | Cache Layer | In-memory Cache | Hot config, semantic response cache, idempotency keys, token buckets | Redis 7 (ElastiCache) | Managed cache |
| 18 | Time-series Metrics Store | Time-series DB | High-volume metric ingestion and analytical rollups | TimescaleDB extension on PostgreSQL or ClickHouse | Managed DB |
| 19 | Observability Stack | Monitoring/Logging | Traces, metrics, logs, alerting, SLO dashboards | OpenTelemetry, Prometheus, Grafana, Loki, Tempo, Sentry | Managed or self-hosted |
| 20 | Secrets and KMS | Security Service | Encryption keys, token secrets, credential protection | AWS KMS + Secrets Manager | Managed security |
| 21 | Feature Flag Service | Config Service | Safe rollout for prompts/models/rules | LaunchDarkly or OpenFeature + Redis | Managed SaaS |
| 22 | Data Warehouse | Analytics/Learning | Long-term analytics, cohort reporting, model evaluation datasets | BigQuery or Snowflake | Managed warehouse |

---

## 1.2 Data Flow Diagram (Textual, Precise)

### Path A: Upload design and company brief -> generated content package

1. User uploads media.
   1. Dashboard requests upload URL from Core API.
   2. Core API validates MIME and file size, returns S3 presigned URL and media_id.
   3. Dashboard uploads binary file directly to S3.
   4. Core API stores media_assets row with status=uploaded.
   5. Event emitted: media.uploaded.v1 (JSON event envelope).

Event schema:

```json
{
  "event_id": "uuid",
  "event_type": "media.uploaded.v1",
  "tenant_id": "uuid",
  "company_id": "uuid",
  "media_id": "uuid",
  "s3_key": "string",
  "mime_type": "image/png",
  "uploaded_at": "ISO-8601"
}
```

2. User submits company brief.
   1. Dashboard calls POST /v1/onboarding/company-profile.
   2. Core API validates against onboarding schema.
   3. Core API writes companies, brand_profiles draft, optional competitors.
   4. Event emitted: company.profile.submitted.v1.

3. Content analysis starts asynchronously.
   1. Content Analysis Service consumes company.profile.submitted.v1.
   2. Service fetches text corpora from PostgreSQL and optional CSV/JSON archive from S3.
   3. NLP processing: NER, sentiment, topic modeling, TF-IDF, engagement correlation.
   4. Service writes brand_profiles.tone_fingerprint_json.
   5. Embeddings generated and stored in brand_voice_embeddings (pgvector).
   6. Event emitted: brand.voice.ready.v1.

4. Visual analysis starts asynchronously.
   1. Visual Service consumes media.uploaded.v1.
   2. Image downloaded from S3, OCR extracted, palette and layout inferred.
   3. Structured visual profile JSON stored in brand_profiles.visual_style_json and media_analysis.
   4. Event emitted: brand.visual.ready.v1.

5. User creates a post generation request.
   1. Dashboard calls POST /v1/posts/generate.
   2. Core API validates payload and inserts posts(status=generating).
   3. Event emitted: post.generation.requested.v1.

6. LLM orchestration builds full context.
   1. LLM Orchestration Service consumes generation event.
   2. Reads profile and tone JSON (PostgreSQL), visual profile (PostgreSQL), top prior posts (pgvector), hashtag performance priors (PostgreSQL), audience priors (time-series aggregates), platform constraints (Redis).
   3. Creates immutable generation_context JSON snapshot and stores in posts.context_snapshot_json.

7. Parallel module execution.
   1. Hashtag/SEO Service receives context and returns ranked hashtags + SEO draft JSON.
   2. Audience Service returns audience object JSON.
   3. Time Optimization Service returns ranked windows with confidence JSON.
   4. Caption Engine calls LLM, returns minimum three variants per platform with scoring metadata.
   5. Each service emits module.result.ready.v1.

8. Consolidation and scoring.
   1. Orchestrator waits on required outputs with timeout fence.
   2. Scoring rubric applied to variants.
   3. Top variant selected; final content package assembled.
   4. posts.generated_package_json updated; post_variants rows inserted.
   5. Status transitions to generated.

9. Delivery.
   1. If synchronous mode, Core API returns package immediately.
   2. If asynchronous mode, frontend polls or listens via WebSocket event post.generation.completed.v1.

Data formats used:

1. Binary: media bytes in S3.
2. JSON: API request/response, service payloads.
3. Event messages: Avro or JSON Schema v1 envelopes on Kafka.
4. Embeddings: float32[] vectors.
5. Metrics: numeric columns + JSON attributes.

---

### Path B: Scheduler trigger -> platform publish -> performance ingestion

1. Schedule created.
   1. Dashboard calls POST /v1/schedules.
   2. Core API validates queue conflicts and inserts schedules rows per platform.
   3. Temporal workflow created with run_at_utc timers.

2. Timer fires.
   1. Scheduler worker picks due job.
   2. Worker loads selected caption, hashtags, media refs, and platform credentials metadata.
   3. Encrypted tokens are decrypted via KMS envelope decryption.

3. Approval gate.
   1. If mode is human and not approved, workflow pauses and sends notification.
   2. If mode is auto or approved, workflow continues.

4. Publish handoff to platform adapters.
   1. Worker calls POST /internal/platform/{platform}/publish.
   2. Payload format is canonical JSON.

Canonical publish payload:

```json
{
  "schedule_id": "uuid",
  "company_id": "uuid",
  "platform": "instagram",
  "content": {
    "caption_text": "string",
    "hashtags": ["#a", "#b"],
    "media": [{"s3_key": "string", "mime_type": "image/jpeg"}],
    "alt_text": "string"
  },
  "tracking": {
    "campaign_tag": "string",
    "utm": {
      "source": "instagram",
      "medium": "social",
      "campaign": "spring_launch"
    }
  }
}
```

5. External API publish.
   1. Adapter maps canonical payload to platform-specific format.
   2. Adapter calls external API with OAuth bearer token.
   3. On success: stores external_post_id, sets schedule status published, emits post.published.v1.
   4. On failure: increments retry_count, computes exponential backoff with jitter, emits post.publish.failed.v1.

6. Analytics ingestion.
   1. Pull path: periodic analytics pulls from platform endpoints.
   2. Webhook path: platform callback events received and validated.
   3. Adapter normalizes to canonical metrics schema.

Canonical metrics schema:

```json
{
  "company_id": "uuid",
  "post_id": "uuid",
  "platform": "instagram",
  "external_post_id": "string",
  "impressions": 12345,
  "reach": 10021,
  "engagement_rate": 0.074,
  "click_through_rate": 0.019,
  "saves": 210,
  "shares": 88,
  "follower_growth_delta": 34,
  "posting_timestamp": "ISO-8601",
  "captured_at": "ISO-8601",
  "source": "webhook"
}
```

7. Metrics persistence and learning.
   1. Core API writes performance_metrics.
   2. Time-series rows inserted into Timescale hypertable.
   3. Event emitted performance.metrics.ingested.v1.
   4. Learning jobs update hashtag scores, posting-window effectiveness, prompt version performance.
   5. If rolling degradation threshold is crossed, event emitted prompt.recalibration.required.v1.

---

## 1.3 Storage Architecture

### 1.3.1 Relational Operational Storage

| Field | Value |
|---|---|
| Technology | PostgreSQL 15 |
| Why | ACID consistency, rich indexing, mature RLS, strong JSONB support |
| Primary Data | users, companies, brand_profiles, posts, post_variants, schedules, platform_credentials, prompt_templates |
| Access Pattern | OLTP writes, indexed reads, transactional updates |
| Retention | 7 years for business records; soft-delete supported |
| Archival | Monthly cold export to S3 parquet, immutable snapshots |

Core relationships:

1. companies 1:N users via memberships.
2. companies 1:N posts.
3. posts 1:N post_variants.
4. posts 1:N schedules.
5. companies 1:N platform_credentials.
6. posts 1:N performance_metrics.

### 1.3.2 Vector Storage

| Field | Value |
|---|---|
| Technology | pgvector extension on PostgreSQL |
| Why | Joinable metadata, reduced infra complexity, transactional updates |
| Data | brand_voice_embeddings, hashtag_embeddings, post_archive_embeddings, audience_profile_embeddings |
| Access Pattern | kNN cosine with metadata filter by tenant/platform |
| Retention | Active vectors indefinite; stale vectors re-embedded after 18 months |
| Archival | Quarterly vector dumps + metadata snapshots |

### 1.3.3 Object Storage

| Field | Value |
|---|---|
| Technology | Amazon S3 |
| Data | Uploaded images/videos, logos, PDFs, generated derivatives |
| Access Pattern | Presigned PUT, signed GET |
| Retention | 24 months default media retention |
| Archival | S3 IA at 90 days, Glacier at 365 days |

### 1.3.4 Cache Storage

| Field | Value |
|---|---|
| Technology | Redis 7 |
| Data | Prompt template hot cache, company config cache, semantic response cache, idempotency keys, rate counters |
| Access Pattern | Read-heavy, TTL-based |
| Retention | 5 minutes to 24 hours by key class |
| Archival | None |

### 1.3.5 Time-series Metrics Storage

| Field | Value |
|---|---|
| Technology | TimescaleDB |
| Data | performance snapshots, webhook event metrics, hourly/day rollups |
| Access Pattern | High write ingestion, aggregation and trend reads |
| Retention | Raw 180 days; hourly rollups 24 months |
| Archival | Monthly export to warehouse |

---

## 1.4 API Surface

### 1.4.1 External Core API endpoints

| Method | Route | Auth | Rate Limit | Purpose |
|---|---|---|---|---|
| POST | /v1/onboarding/company-profile | JWT (OIDC) | 30/min/user | Submit onboarding profile |
| POST | /v1/media/presign | JWT | 120/min/user | Request upload URL |
| POST | /v1/posts/generate | JWT | 20/min/company | Request content package generation |
| GET | /v1/posts/{post_id}/generation-result | JWT | 120/min/user | Fetch generated output |
| POST | /v1/schedules | JWT | 60/min/company | Create schedule entries |
| POST | /v1/schedules/{schedule_id}/approve | JWT + role check | 60/min/company | Human approval |
| POST | /v1/platform/publish-now | JWT | 10/min/company | Immediate publish |
| POST | /v1/analytics/ingest | API key + HMAC | 600/min/company | Manual analytics ingestion |
| POST | /v1/llm/proxy/chat | Service token only | 300/min/service | LLM proxy endpoint |
| GET | /v1/platform/oauth/{platform}/connect | JWT | 30/min/user | OAuth start |
| GET | /v1/platform/oauth/{platform}/callback | OAuth state + PKCE | N/A | OAuth callback |

### 1.4.2 Internal Service API endpoints

| Method | Route | Auth | Purpose |
|---|---|---|---|
| POST | /internal/content-analysis/run | mTLS + service JWT | NLP run |
| POST | /internal/visual-analysis/run | mTLS + service JWT | Visual run |
| POST | /internal/hashtags/generate | mTLS + service JWT | Hashtag and SEO run |
| POST | /internal/audience/generate | mTLS + service JWT | Audience run |
| POST | /internal/time-optimize/rank | mTLS + service JWT | Posting window rank |
| POST | /internal/captions/generate | mTLS + service JWT | Caption generation |
| POST | /internal/platform/{platform}/publish | mTLS + service JWT | Publish adapter |
| POST | /internal/platform/{platform}/metrics/pull | mTLS + service JWT | Analytics pull |
| POST | /internal/webhooks/{platform} | Platform secret/HMAC | Callback ingestion |

### 1.4.3 Required request/response schemas

Company onboarding API:

```json
{
  "method": "POST",
  "route": "/v1/onboarding/company-profile",
  "request_schema": {
    "company_name": "string(2..120)",
    "industry_vertical": "string",
    "target_market": {
      "regions": ["ISO-3166-1 alpha-2"],
      "segments": ["B2B|B2C|D2C"],
      "persona_summary": "string"
    },
    "brand_positioning_statement": "string(30..500)",
    "tone_of_voice_descriptors": ["string"],
    "competitor_list": ["string"],
    "platform_presence": {
      "instagram": "boolean",
      "linkedin": "boolean",
      "facebook": "boolean",
      "x": "boolean",
      "tiktok": "boolean",
      "pinterest": "boolean"
    },
    "posting_frequency_goal": {
      "instagram": "int",
      "linkedin": "int",
      "facebook": "int",
      "x": "int",
      "tiktok": "int",
      "pinterest": "int"
    },
    "primary_cta_types": ["string"],
    "brand_color_hex_codes": ["#RRGGBB"],
    "approved_vocabulary_list": ["string"],
    "banned_vocabulary_list": ["string"],
    "previous_post_archive": {"format": "csv|json", "s3_uri": "string?"},
    "brand_guidelines_pdf": "s3_uri?",
    "logo_file": "media_id?",
    "sample_post_images": ["media_id?"]
  },
  "response_schema": {
    "company_id": "uuid",
    "profile_version": "int",
    "status": "submitted"
  }
}
```

Post generation API:

```json
{
  "method": "POST",
  "route": "/v1/posts/generate",
  "request_schema": {
    "company_id": "uuid",
    "post_intent": "announce|educate|promote|engage|inspire|crisis_response",
    "core_message": "string(20..500)",
    "target_platforms": ["instagram|linkedin|facebook|x|tiktok|pinterest"],
    "campaign_tag": "string?",
    "attached_media_id": "uuid?",
    "manual_keywords": ["string"],
    "urgency_level": "scheduled|immediate",
    "requested_publish_at": "ISO-8601?"
  },
  "response_schema": {
    "post_id": "uuid",
    "status": "generating|generated",
    "estimated_ready_seconds": "int"
  }
}
```

Scheduling API:

```json
{
  "method": "POST",
  "route": "/v1/schedules",
  "request_schema": {
    "post_id": "uuid",
    "company_id": "uuid",
    "targets": [
      {
        "platform": "instagram|linkedin|facebook|x|tiktok|pinterest",
        "run_at_utc": "ISO-8601"
      }
    ],
    "approval_mode": "human|auto",
    "manual_override": {
      "timezone": "IANA",
      "force_window": "boolean"
    }
  },
  "response_schema": {
    "schedule_ids": ["uuid"],
    "status": "queued"
  }
}
```

Platform publishing API:

```json
{
  "method": "POST",
  "route": "/internal/platform/{platform}/publish",
  "request_schema": {
    "schedule_id": "uuid",
    "company_id": "uuid",
    "platform": "string",
    "content": {
      "caption_text": "string",
      "hashtags": ["string"],
      "media": [{"s3_key": "string", "mime_type": "string"}],
      "alt_text": "string?"
    },
    "credentials_ref": "uuid",
    "idempotency_key": "string"
  },
  "response_schema": {
    "status": "published|failed",
    "external_post_id": "string?",
    "error": {"code": "string", "message": "string"}
  }
}
```

Analytics ingestion API:

```json
{
  "method": "POST",
  "route": "/v1/analytics/ingest",
  "request_schema": {
    "records": [
      {
        "post_id": "uuid",
        "platform": "string",
        "external_post_id": "string",
        "impressions": "int",
        "reach": "int",
        "engagement_rate": "float",
        "click_through_rate": "float",
        "saves": "int",
        "shares": "int",
        "follower_growth_delta": "int",
        "posting_timestamp": "ISO-8601",
        "captured_at": "ISO-8601"
      }
    ]
  },
  "response_schema": {
    "ingested_count": "int",
    "rejected_count": "int",
    "errors": [{"index": "int", "reason": "string"}]
  }
}
```

LLM proxy API:

```json
{
  "method": "POST",
  "route": "/v1/llm/proxy/chat",
  "request_schema": {
    "provider": "deepseek|openai|anthropic|mistral",
    "model": "string",
    "messages": [{"role": "system|user|assistant", "content": "string"}],
    "response_format": "json|text",
    "temperature": "float(0..1)",
    "max_tokens": "int",
    "cache_key": "string?"
  },
  "response_schema": {
    "provider_used": "string",
    "model_used": "string",
    "output": "string|json",
    "token_usage": {"input": "int", "output": "int"},
    "cached": "boolean"
  }
}
```

### 1.4.4 Error handling strategy

| Category | HTTP | Strategy |
|---|---|---|
| Validation | 400 | Return field-level errors, reject write |
| Auth/AuthZ | 401/403 | Reject and audit |
| Not found | 404 | Traceable error envelope |
| Conflict | 409 | Idempotency or schedule collision details |
| Rate limit | 429 | Retry-After header, token bucket counters |
| Transient upstream | 503 | Retryable=true, exponential backoff |
| Internal | 500 | Correlation ID + alert trigger |

Standard error envelope:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {},
    "trace_id": "uuid",
    "retryable": true
  }
}
```

---

## 1.5 Automation Layers

### 1.5.1 Layer 1 - Rule-based deterministic logic

| Dimension | Definition |
|---|---|
| Ownership | Validation, policy enforcement, fixed transformations, safe defaults |
| Inputs | User payloads, platform constraints, banned vocab lists, schedule policies |
| Outputs | Canonical validated payloads, filtered candidates, deterministic ranking baselines |
| Typical Decisions | Char limits, hashtag caps, schedule conflicts, cooldown windows, OAuth refresh timing |

### 1.5.2 Layer 2 - AI-assisted generation

| Dimension | Definition |
|---|---|
| Ownership | Caption variants, audience psychographics, tone calibration, SEO metadata |
| Inputs | Tone fingerprint, visual analysis, audience priors, post intent, historical examples |
| Outputs | Structured JSON artifacts with confidence scores and rationales |
| Typical Decisions | Linguistic framing, CTA wording, semantic hashtag suggestions |

### 1.5.3 Layer 3 - Self-improving feedback loop

| Dimension | Definition |
|---|---|
| Ownership | Post-performance labeling, prompt version scoring, drift detection, recalibration triggers |
| Inputs | Engagement metrics, publish outcomes, quality scores, platform-level trends |
| Outputs | Updated prompt template versions, ranking weight adjustments, recalibration jobs |
| Typical Decisions | Activate new prompt version if uplift >= threshold, trigger retraining if degradation detected |
