import { NextResponse } from "next/server";

export function retiredFrontendProviderRoute(feature: string): NextResponse {
  return NextResponse.json(
    {
      code: "FRONTEND_PROVIDER_ROUTE_RETIRED",
      message:
        "This frontend provider endpoint is retired. Normal ARIA product flows must call the llm-orchestration backend instead of OpenAI or Anthropic from Next.js route handlers.",
      feature,
      canonical_api: {
        base_env: "NEXT_PUBLIC_AI_ORCHESTRATION_URL",
        content_generation: "/internal/ai/generate-content-package",
        post_generation: "/v1/posts/generate"
      }
    },
    {
      status: 410,
      headers: {
        "X-ARIA-Deprecated-Route": "frontend-provider-direct"
      }
    }
  );
}

