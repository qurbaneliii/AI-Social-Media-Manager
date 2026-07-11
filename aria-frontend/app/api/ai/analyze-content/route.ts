import { retiredFrontendProviderRoute } from "@/lib/api/deprecated-provider-route";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  await request.body?.cancel();
  return retiredFrontendProviderRoute("legacy-openai-analyze-content");
}
