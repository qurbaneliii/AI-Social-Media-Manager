# Deployment Environment Variables

Do not commit real secrets. Do not put backend secrets in frontend public variables.

## Render Backend

Service: `aria-llm-orchestration`

| Variable | Required | Value for free MVP | Notes |
| --- | --- | --- | --- |
| `DATABASE_URL` | Yes | From Supabase Dashboard Connect | Backend-only. Never expose in Vercel. |
| `AI_MOCK_MODE` | Yes | `true` | Keeps demo free of paid OpenAI API calls. |
| `OPENAI_API_KEY` | Yes | `replace-me` | Mock mode ignores this placeholder. |
| `OPENAI_MODEL` | Yes | `gpt-4o-mini` | Used if real mode is enabled later. |
| `AI_TEMPERATURE` | Yes | `0.4` | LLM setting. |
| `AI_MAX_RETRIES` | Yes | `2` | LLM retry setting. |
| `AI_REQUEST_TIMEOUT_SECONDS` | Yes | `30` | LLM request timeout. |
| `CORS_ORIGINS` | Yes | Final Vercel URL | Use exact URL, not wildcard, after frontend deploy. |

Optional backend variables from repo examples may be added only if the broader API stack is deployed. They are not required for the LLM orchestration MVP demo.

## Vercel Frontend

Project root: `aria-frontend`

| Variable | Required | Value for free MVP | Notes |
| --- | --- | --- | --- |
| `NEXT_PUBLIC_AI_ORCHESTRATION_URL` | Yes | Render backend URL | Public browser URL for FastAPI orchestration service. |
| `NEXT_PUBLIC_API_BASE_URL` | Optional | Render backend URL | Compatibility fallback for older client helpers. |
| `NEXT_PUBLIC_API_URL` | Optional | Render backend URL | Compatibility fallback for older client helpers. |
| `NEXT_PUBLIC_PREVIEW_MODE` | Optional | `true` | Enables preview/demo framing in UI. |
| `NEXT_PUBLIC_AI_REQUEST_TIMEOUT_MS` | Optional | `45000` | Browser-side AI request timeout. |
| `NEXT_PUBLIC_AI_REQUEST_RETRIES` | Optional | `2` | Browser-side retry count. |

Do not configure these as frontend public variables:

- `DATABASE_URL`
- Supabase service role key
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- Render secrets
- Any social media OAuth client secret

## Supabase

Project:

- Name: `aria-mvp-demo`
- Ref: `bypwigurvhlqjhrlgckf`
- API URL: `https://bypwigurvhlqjhrlgckf.supabase.co`

Backend connection:

- Use Supabase Dashboard > Connect to copy the pooled or direct PostgreSQL connection string.
- Store it only as Render `DATABASE_URL`.
- Do not commit it.
- Do not store it in Vercel public environment variables.

## Real OpenAI Mode Later

The deployed MVP should start with:

```text
AI_MOCK_MODE=true
OPENAI_API_KEY=replace-me
```

If real OpenAI mode is later enabled:

```text
AI_MOCK_MODE=false
OPENAI_API_KEY=<real backend-only key>
```

OpenAI API billing is separate from Vercel, Render, and Supabase and is not free.
