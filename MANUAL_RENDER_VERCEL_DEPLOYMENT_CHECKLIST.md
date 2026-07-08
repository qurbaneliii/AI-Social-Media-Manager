# Manual Render/Vercel Deployment Checklist

Use this checklist only for the provider-side steps that connected tools could not perform. Do not paste secrets into GitHub, Vercel public env vars, docs, screenshots, or chat.

## Supabase Checklist

1. Open Supabase project `aria-mvp-demo`.
2. Confirm project ref is `bypwigurvhlqjhrlgckf`.
3. Go to Dashboard -> Connect.
4. Copy a backend/server PostgreSQL connection string.
5. Use the correct database password in the connection string.
6. Do not paste this value into Vercel frontend env vars.
7. Paste it only into Render `DATABASE_URL`.

Verification:

- Supabase project still shows healthy.
- `vector` remains enabled.
- These tables still exist:
  - `ai_brand_memory`
  - `ai_content_drafts`
  - `ai_quality_reviews`
  - `ai_calendar_draft_items`
  - `ai_community_reply_drafts`
  - `ai_report_drafts`
  - `ai_approval_audit_events`

## Render Checklist

1. Go to Render Dashboard.
2. Choose New -> Web Service.
3. Connect GitHub repo `qurbaneliii/AI-Social-Media-Manager`.
4. Select branch `deploy/mvp-vercel-render-supabase`.
5. Set service name `aria-ai-orchestration-mvp`.
6. Set root directory `aria/apps/llm-orchestration`.
7. Set runtime `Python`.
8. Set plan `Free`.
9. Set build command:

```bash
pip install -U pip && pip install -e .
```

10. Set start command:

```bash
PYTHONPATH=app uvicorn main:app --host 0.0.0.0 --port $PORT
```

11. Set environment variables:

```text
DATABASE_URL=<copy from Supabase Dashboard Connect>
AI_MOCK_MODE=true
OPENAI_API_KEY=replace-me
OPENAI_MODEL=gpt-4o-mini
AI_TEMPERATURE=0.4
AI_MAX_RETRIES=2
AI_REQUEST_TIMEOUT_SECONDS=30
CORS_ORIGINS=http://localhost:3000
```

12. Deploy the service.
13. Copy the Render backend URL.
14. Test these URLs:

```text
https://<render-service>.onrender.com/health
https://<render-service>.onrender.com/docs
https://<render-service>.onrender.com/openapi.json
https://<render-service>.onrender.com/internal/ai/workspace-context
```

Expected result:

- `/health` returns healthy JSON.
- `/docs` or `/openapi.json` opens.
- `/internal/ai/workspace-context` returns structured workspace JSON in mock mode.

## Vercel Checklist

1. Go to Vercel Dashboard.
2. Choose New Project.
3. Import GitHub repo `qurbaneliii/AI-Social-Media-Manager`.
4. Select branch `deploy/mvp-vercel-render-supabase`.
5. Use project name `aria-ai-social-media-manager-mvp`.
6. Set root directory `aria-frontend`.
7. Set framework `Next.js`.
8. Set install command:

```bash
npm install
```

9. Set build command:

```bash
npm run build
```

10. Set environment variable:

```text
NEXT_PUBLIC_AI_ORCHESTRATION_URL=<Render backend URL>
```

11. Do not set any of these in Vercel:

```text
DATABASE_URL
OPENAI_API_KEY
SUPABASE_SERVICE_ROLE_KEY
Any Supabase database password
Any social OAuth client secret
```

12. Deploy.
13. Copy the Vercel production URL.
14. Test these routes:

```text
https://<vercel-app>.vercel.app/
https://<vercel-app>.vercel.app/login
https://<vercel-app>.vercel.app/dashboard/ai
https://<vercel-app>.vercel.app/dashboard/brand-brain
https://<vercel-app>.vercel.app/dashboard/content-studio
https://<vercel-app>.vercel.app/dashboard/approval
```

Expected result:

- The Next.js frontend loads from Vercel.
- Dashboard routes do not return Vercel `404`.
- If auth appears, use the preview-user flow described in the app.

## Final CORS Checklist

1. Go back to Render service `aria-ai-orchestration-mvp`.
2. Replace:

```text
CORS_ORIGINS=http://localhost:3000
```

3. With:

```text
CORS_ORIGINS=<exact Vercel production URL>
```

4. Redeploy or restart Render.
5. Open the Vercel production URL.
6. Verify frontend-to-backend calls do not show CORS errors.

## End-To-End MVP Checklist

- Frontend production URL opens.
- Render backend `/docs` opens.
- Render backend `/openapi.json` opens.
- `/internal/ai/workspace-context` returns data.
- Brand Brain validation works.
- Content Studio returns mock content.
- Strategy returns a structured mock response.
- Calendar AI returns draft/planning data.
- Community AI returns suggested reply only.
- Approval page loads.
- No auto-publish exists.
- No auto-reply exists.
- No real scheduling exists.
- Supabase project remains healthy.

## Message To Send Back To Codex

After completing the manual provider steps, send:

```text
Render URL: <paste Render URL>
Vercel URL: <paste Vercel production URL>
I set DATABASE_URL in Render only.
I set NEXT_PUBLIC_AI_ORCHESTRATION_URL in Vercel.
I updated Render CORS_ORIGINS to the Vercel URL.
Please verify the deployed MVP end-to-end.
```
