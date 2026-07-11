import { retiredFrontendProviderRoute } from "@/lib/api/deprecated-provider-route";

export const dynamic = "force-dynamic";

export async function POST(request: Request): Promise<Response> {
  await request.body?.cancel();
  return retiredFrontendProviderRoute("legacy-anthropic-streaming-generate");
}
